#
# Copyright (c) 2015, Adam Meily <meily.adam@gmail.com>
# Pypsi - https://github.com/ameily/pypsi
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import sys
import os
import readline
from typing import Union, List, Dict
from pypsi.cmdline import (StatementParser, StatementSyntaxError, IORedirectionError,
                           CommandNotFoundError, StringToken, OperatorToken, Token, WhitespaceToken,
                           UnclosedQuotationError, TrailingEscapeError)

from pypsi.namespace import Namespace
from pypsi.completers import path_completer
from pypsi.os import is_path_prefix
from pypsi.ansi import Color, pypsi_print, ThreadLocalAnsiStream
from pypsi.profiles import BashProfile, TabCompletionProfile, ShellProfile
from pypsi.core import Plugin, Command
from pypsi.pipes import InvocationThread
from pypsi.proxy import ThreadLocalProxy
from .os import make_ansi_stream


class Shell:
    '''
    The command line interface that the user interacts with. All shell's need
    to inherit this base class.
    '''
    # pylint: disable=too-many-public-methods,too-many-instance-attributes

    def __init__(self, shell_name: str = 'pypsi', width: int = None, exit_rc: int = -1024,
                 ctx: Namespace = None, profile: ShellProfile = None, completer_delims: str = None,
                 colors: bool = True, max_width: int = None):
        '''
        Subclasses need to call the Shell constructor to properly initialize
        it.

        :param str shell_name: the name of the shell; used in error messages
        :param int exit_rc: the exit return code that is returned from a
            command when the shell needs to end execution
        :param pypsi.namespace.Namespace ctx: the base context
        '''
        # pylint: disable=too-many-arguments
        self.backup_stdout = None
        self.backup_stdin = None
        self.backup_stderr = None
        self.backup_print = None

        self.shell_name = shell_name
        self.exit_rc = exit_rc
        self.errno = 0
        self.commands: Dict[str, Command] = {}
        self.preprocessors: List[Plugin] = []
        self.postprocessors: List[Plugin] = []
        self.plugins = []
        self.prompt = f"{shell_name} )> "
        self.ctx = ctx or Namespace()
        self.profile = profile or BashProfile()
        self.running = False
        self.completion_matches = None
        self.completer_delims = completer_delims
        self.colors = colors

        self.register_base_plugins()
        self.fallback_cmd: Command = None

        self.eof_is_sigint = False
        self._backup_completer = readline.get_completer()
        self.width = width
        self.max_width = max_width

        self.bootstrap()

        self.on_shell_ready()

    def bootstrap(self) -> None:
        import builtins  # pylint: disable=import-outside-toplevel
        if not isinstance(sys.stdout, ThreadLocalAnsiStream):
            self.backup_stdout = sys.stdout
            stream = make_ansi_stream(sys.stdout)
            sys.stdout = ThreadLocalAnsiStream(stream, width=self.width, max_width=self.max_width,
                                               ansi=self.colors)

        if not isinstance(sys.stderr, ThreadLocalAnsiStream):
            self.backup_stderr = sys.stderr
            stream = make_ansi_stream(sys.stderr)
            sys.stderr = ThreadLocalAnsiStream(stream, width=self.width, max_width=self.max_width,
                                               ansi=self.colors)

        if not isinstance(sys.stdin, ThreadLocalProxy):
            self.backup_stdin = sys.stdin
            sys.stdin = ThreadLocalProxy(sys.stdin)

        if builtins.print is not pypsi_print:  # pylint: disable=comparison-with-callable
            self.backup_print = print
            builtins.print = pypsi_print

    def restore(self) -> None:
        if self.backup_stdout:
            sys.stdout = self.backup_stdout

        if self.backup_stderr:
            sys.stderr = self.backup_stderr

        if self.backup_stdin:
            sys.stdin = self.backup_stdin

        if self.backup_print:
            import builtins  # pylint: disable=import-outside-toplevel
            builtins.print = self.backup_print

    def register_base_plugins(self) -> None:
        '''
        Register all base plugins that are defined.
        '''

        cls = self.__class__
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, (Command, Plugin)):
                self.register(attr)

    def register(self, obj: Union[Plugin, Command]) -> None:
        '''
        Register a :class:`~pypsi.core.Command` or a
        :class:`~pypsi.core.Plugin`.
        '''

        if isinstance(obj, Command):
            self.commands[obj.name] = obj

        if isinstance(obj, Plugin):
            self.plugins.append(obj)
            if obj.preprocess is not None:
                self.preprocessors.append(obj)
                self.preprocessors = sorted(self.preprocessors,
                                            key=lambda x: x.preprocess)
            if obj.postprocess is not None:
                self.postprocessors.append(obj)
                self.postprocessors = sorted(self.postprocessors,
                                             key=lambda x: x.postprocess)

        obj.setup(self)

    def on_shell_ready(self) -> None:
        '''
        Hook that is called after the shell has been created.
        '''

    def on_cmdloop_begin(self) -> None:
        '''
        Hook that is called once the :meth:`cmdloop` function is called.
        '''

    def on_cmdloop_end(self) -> None:
        '''
        Hook that is called once the :meth:`cmdloop` has ended.
        '''

    def get_current_prompt(self) -> str:
        if callable(self.prompt):
            prompt = self.prompt()  # pylint: disable=not-callable
        else:
            prompt = self.prompt

        return self.preprocess_single(prompt, 'prompt')

    def set_readline_completer(self) -> None:
        if readline.get_completer() != self.complete:  # pylint: disable=comparison-with-callable
            readline.parse_and_bind("tab: complete")
            self._backup_completer = readline.get_completer()
            readline.set_completer(self.complete)
            if self.completer_delims is not None:
                readline.set_completer_delims(self.completer_delims)

    def reset_readline_completer(self) -> None:
        if readline.get_completer() == self.complete:  # pylint: disable=comparison-with-callable
            readline.set_completer(self._backup_completer)

    def on_input_canceled(self) -> None:
        for pp in self.preprocessors:
            pp.on_input_canceled(self)

    def on_tokenize(self, tokens, origin) -> List[Token]:
        for pp in self.preprocessors:
            tokens = pp.on_tokenize(self, tokens, origin)
            if not tokens:
                break
        return tokens

    def include(self, file: str):
        '''
        Read commands from a file and execute them line by line

        :param file file: File object to read commands from
        :return int: 0 if error free; 1 if an error occurred
        '''
        rc = 1
        eof = False

        # set STDIN to the file
        stdin = sys.stdin._get_target()  # pylint: disable=protected-access
        sys.stdin._proxy(file)  # pylint: disable=protected-access

        try:
            raw = sys.stdin.readline()
            while not eof and raw:
                raw = raw.rstrip()

                rc = None
                try:
                    rc = self.execute(raw)
                except SystemExit as e:
                    rc = e.code
                    eof = True
                else:
                    rc = rc or 0
                    raw = sys.stdin.readline()
                finally:
                    if rc is not None:
                        self.errno = rc

                    for pp in self.postprocessors:
                        pp.on_statement_finished(self, rc)
        except (EOFError, KeyboardInterrupt):
            print()
            self.on_input_canceled()
            rc = 0
        finally:
            # Reset stdin to a tty
            sys.stdin._proxy(stdin)  # pylint: disable=protected-access
        return rc

    def cmdloop(self):
        '''
        Begin the input processing loop where the user will be prompted for
        input.
        '''
        # pylint: disable=too-many-branches
        self.running = True
        self.set_readline_completer()
        self.on_cmdloop_begin()
        rc = 0
        try:
            while self.running:
                try:
                    raw = input(self.get_current_prompt())
                except EOFError:
                    print()
                    self.on_input_canceled()
                    if not self.profile.eof_is_sigint:
                        self.running = False
                        print("exiting....")
                except KeyboardInterrupt:
                    print()
                    self.on_input_canceled()
                else:
                    rc = None
                    if self.width is None:
                        sys.stdout.detect_width()
                        sys.stderr.detect_width()

                    try:
                        rc = self.execute(raw)
                        rc = rc or 0
                    except SystemExit as e:
                        rc = e.code
                        print("exiting....")
                        self.running = False
                    except KeyboardInterrupt:
                        # Bash returns 130 if a command was interrupted
                        rc = None
                        print()
                    except EOFError:
                        # Bash returns 1 for Ctrl+D
                        rc = None
                        print()
                    finally:
                        if rc is not None:
                            self.errno = rc

                        for pp in self.postprocessors:
                            pp.on_statement_finished(self, rc)
        finally:
            self.on_cmdloop_end()
            self.reset_readline_completer()
        return rc

    def error(self, msg):
        print(Color.bright_red(self.shell_name, ": ", msg), file=sys.stderr)

    def mkpipe(self):
        r, w = os.pipe()
        return (
            os.fdopen(r, 'r'),
            os.fdopen(w, 'w')
        )

    def execute(self, raw):
        '''
        Parse and execute a statement.

        :param str raw: the raw command line to parse.
        :param function input: a function that returns a string,
                                overrides default input function (stdin).
        :returns int: the return code of the statement.
        '''
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        parser = StatementParser(self.profile)
        input_complete = False
        while not input_complete:
            text = self.preprocess(raw, 'input')
            if text is None:
                return None

            try:
                tokens = parser.tokenize(text)
            except (UnclosedQuotationError, TrailingEscapeError):
                input_complete = False
            else:
                # Parsing succeeded, break out of the input loop
                input_complete = True

            if not input_complete:
                # This is a multiline input
                try:
                    # hide prompt if reading from a file
                    raw = input("> " if sys.stdin.isatty() else '')
                except (EOFError, KeyboardInterrupt) as e:
                    self.on_input_canceled()
                    raise e

        tokens = self.on_tokenize(tokens, 'input')
        statement = None

        if not tokens:
            return None

        try:
            statement = parser.build(tokens)
        except StatementSyntaxError as e:
            self.error(str(e))
            return 1

        rc = None

        if not statement:
            # The line was empty, a comment, or just contained whitespace.
            return rc

        # Setup the invocations
        for invoke in statement:
            try:
                # Open any and all I/O redirections and resolve the pypsi
                # command.
                invoke.setup(self)
            except Exception as e:
                for sub in statement:
                    sub.close_streams()

                if isinstance(e, (IORedirectionError, CommandNotFoundError)):
                    # pypsi can handle I/O redirection and command not found
                    # errors, these are not fatal.
                    self.error(str(e))
                    return -1
                # Unhandled fatal exception, re-raise it
                raise

        # Current pipe being built
        pipe = []

        # Process the statement
        for invoke in statement:
            if invoke.chain_pipe():
                # We are in a pipe
                pipe.append(invoke)
            else:
                # We are not in a pipe

                if pipe:
                    # We have a pipe built that needs to be executed.
                    # Create the invocation threads for the pipe.
                    threads, stdin = self.create_pipe_threads(pipe)
                    # Reset the building pipe
                    pipe = []
                    # Set the current invocation's stdin to the last
                    # invocation's stdout.
                    invoke.stdin = stdin
                else:
                    # We were not in a pipe
                    threads = []

                # Start all the pipe threads, if we are processing a pipe
                for t in threads:
                    t.start()

                # Execute the invocation in the current thread.
                try:
                    rc = invoke(self)
                except Exception as e:  # pylint: disable=broad-except
                    # Unhandled exception, stop all threads if any are running.
                    for t in threads:
                        t.stop()

                    # Wait for threads to terminate.
                    try:
                        for t in threads:
                            t.join()
                    except:  # pylint: disable=bare-except
                        # Something went wrong or a KeyboardInterrupt was
                        # issued. Stop waiting for threads to terminate.
                        pass

                    # Print thread-specific unhandled exceptions.
                    for t in threads:
                        if t.exc_info:
                            if t.exc_info[0] == OSError:
                                msg = t.exc_info[1].strerror
                            else:
                                msg = str(t.exc_info[1])

                            print(Color.bright_red(t.invoke.name, ": ", msg), file=sys.stderr)

                    if isinstance(e, KeyboardInterrupt):
                        # Ctrl+c was entered
                        print()
                        rc = -1
                    elif isinstance(e, SystemExit):
                        # The command is requesting to exit the shell.
                        rc = e.code  # pylint: disable=no-member
                        print("exiting....")
                        self.running = False
                    elif isinstance(e, RuntimeError):
                        # The command was aborted by a generic exception.
                        self.error("command aborted: " + str(e))
                        rc = -1
                    else:
                        # Unhandled fatal exception, re-raise it
                        raise

                self.errno = rc

                # Check if the statement's next invocation be executed.
                if not invoke.should_continue(rc):
                    break

        return rc

    def create_pipe_threads(self, pipe):
        '''
        Given a pipe (list of :class:`~pypsi.cmdline.CommandInvocation`
        objects) create a thread to execute for each invocation.

        :returns tuple: a tuple containing the list of threads
            (:class:`~pypsi.pipes.CommandThread`) and the last invocation's
            stdout stream.
        '''

        threads = []
        stdin = None
        for invoke in pipe:
            next_stdin, stdout = self.mkpipe()

            t = InvocationThread(self, invoke, stdin=stdin, stdout=stdout)
            threads.append(t)

            stdin = next_stdin

        return threads, stdin

    def preprocess(self, raw, origin):  # pylint: disable=unused-argument
        for pp in self.preprocessors:
            raw = pp.on_input(self, raw)
            if raw is None:
                break

        return raw

    def preprocess_single(self, raw, origin):
        tokens = self.on_tokenize([StringToken(0, raw, quote='"')], origin)

        if tokens:
            parser = StatementParser(self.profile)
            parser.clean_escapes(tokens)
            ret = ''
            for token in tokens:
                ret += token.text
            return ret
        return ''

    def _clean_completions(self, completions, quotation):
        '''
        Clean completion choices so that they can be displayed to the screen or, if only a single
        completion is available, be inserted into the line buffer.

        :param list[str] completions: list of completions
        :param str quotation: active quotation character
        :returns list[str]: cleaned completions
        '''
        escape = self.profile.escape_char
        quotation = quotation or ''

        if len(completions) == 1:
            ans = completions[0]
            close_quote = ans.endswith('\0')
            if quotation:
                completions[0] = ans.replace(quotation, escape + quotation)
            else:
                completions[0] = ans.replace(escape, escape * 2).replace(' ', escape + ' ')
        else:
            close_quote = False

        for i, ans in enumerate(completions):
            if ans.endswith('\0'):
                ans = ans[:-1]
            if close_quote:
                ans = f'{ans}{quotation} '
            completions[i] = ans

        return completions

    def get_completions(self, line, prefix):
        '''
        Get the list of completions given a line buffer and a prefix.

        :param str line: line buffer content up to cursor
        :param str prefix: readline prefix token
        :returns list[str]: list of completions
        '''
        # pylint: disable=too-many-branches,too-many-statements
        try:
            parser = StatementParser(TabCompletionProfile(self.profile))
            tokens = parser.tokenize(line)
            parser.clean_escapes(tokens)

            cmd_name = ""
            loc = None
            args = []
            next_arg = True
            ret = []
            in_quote = None
            for token in tokens:
                if isinstance(token, StringToken):
                    in_quote = token.quote if token.open_quote else None
                    if not cmd_name:
                        cmd_name = token.text
                        loc = 'name'
                    elif loc == 'name':
                        cmd_name += token.text
                    else:
                        if next_arg:
                            args.append(token.text)
                            next_arg = False
                        else:
                            args[-1] += token.text
                elif isinstance(token, OperatorToken):
                    in_quote = None
                    if token.operator in ('|', ';', '&&', '||'):
                        cmd_name = None
                        args = []
                        next_arg = True
                    elif token.operator in ('>', '<', '>>'):
                        loc = 'path'
                        args = []
                elif isinstance(token, WhitespaceToken):
                    in_quote = None
                    if loc == 'name':
                        loc = None
                    next_arg = True

            if loc == 'path':
                ret = path_completer(''.join(args), prefix)
            elif not cmd_name or loc == 'name':
                if is_path_prefix(cmd_name):
                    ret = path_completer(cmd_name, prefix)
                else:
                    ret = self.get_command_name_completions(cmd_name)
            else:
                if cmd_name not in self.commands:
                    ret = []
                else:
                    if next_arg:
                        args.append('')

                    cmd = self.commands[cmd_name]
                    ret = cmd.complete(self, args, prefix)

            ret = self._clean_completions(ret, in_quote)
        except:  # pylint: disable=bare-except
            ret = []

        return ret

    def get_command_name_completions(self, prefix):
        '''
        Get the list of commands that begin with a given prefix token.

        :param str prefix: command prefix
        :returns list[str]: list of command names that begin with prefix
        '''
        return sorted([cmd for cmd in self.commands if cmd.startswith(prefix)])

    def complete(self, text, state):  # pylint: disable=unused-argument
        '''
        readline tab completion callback.
        '''
        if state == 0:
            self.completion_matches = []
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            line = readline.get_line_buffer()
            prefix = line[begidx:endidx] if line else ''
            line = line[:endidx]
            self.completion_matches = self.get_completions(line, prefix)

        if state < len(self.completion_matches):
            return self.completion_matches[state]
        return None

    def print_completion_matches(self, substitution, matches, max_len):
        print("substitution:", substitution)
        print("matches:     ", matches)
        print("max_len:     ", max_len)
