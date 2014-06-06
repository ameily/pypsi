#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from pypsi.base import Plugin, Command
from pypsi.cmdline import StatementParser, StatementSyntaxError, StatementContext
from pypsi.namespace import Namespace
from pypsi.cmdline import StringToken, OperatorToken, WhitespaceToken
from pypsi.completers import path_completer
import readline
import sys


class Shell(object):
    '''
    The command line interface that the user interacts with. All shell's need to
    inherit this base class.
    '''

    def __init__(self, shell_name='pypsi', width=79, exit_rc=-1024, ctx=None):
        '''
        :param str shell_name: the name of the shell; used in error messages
        :param int exit_rc: the exit return code that is returned from a command
            when the shell needs to end execution
        :param pypsi.namespace.Namespace ctx: the base context
        '''
        self.real_stdout = sys.stdout
        self.real_stdin = sys.stdin
        self.real_stderr = sys.stderr
        self.width = width
        self.shell_name = shell_name
        self.exit_rc = exit_rc
        self.errno = 0
        self.commands = {}
        self.preprocessors = []
        self.postprocessors = []
        self.plugins = []
        self.prompt = "{name} )> ".format(name=shell_name)
        self.ctx = ctx or Namespace()

        self.parser = StatementParser()
        self.default_cmd = None
        self.register_base_plugins()
        self.fallback_cmd = None

        self.on_shell_ready()

    def register_base_plugins(self):
        '''
        Register all base plugins that are defined.
        '''

        cls = self.__class__
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, Command) or isinstance(attr, Plugin):
                self.register(attr)

    def register(self, obj):
        '''
        Register a :class:`~pypsi.base.Command` or a :class:`~pypsi.base.Plugin`.
        '''

        if isinstance(obj, Command):
            self.commands[obj.name] = obj

        if isinstance(obj, Plugin):
            self.plugins.append(obj)
            if obj.preprocess is not None:
                self.preprocessors.append(obj)
                self.preprocessors = sorted(self.preprocessors, key=lambda x: x.preprocess)
            if obj.postprocess is not None:
                self.postprocessors.append(obj)
                self.postprocessors = sorted(self.postprocessors, key=lambda x: x.postprocess)

        obj.setup(self)
        return 0

    def on_shell_ready(self):
        return 0

    def on_cmdloop_begin(self):
        return 0

    def on_cmdloop_end(self):
        return 0

    def get_current_prompt(self):
        return self.preprocess_single(self.prompt, 'prompt')

    def cmdloop(self):
        self.running = True
        self.on_cmdloop_begin()
        readline.parse_and_bind("tab: complete")
        old_completer = readline.get_completer()
        readline.set_completer(self.complete)
        rc = 0
        try:
            while self.running:
                try:
                    raw = input(self.get_current_prompt())
                except EOFError:
                    self.running = False
                    print("exiting....")
                except KeyboardInterrupt:
                    print()
                    for pp in self.preprocessors:
                        pp.on_input_canceled(self)
                else:
                    rc = self.execute(raw)
        finally:
            self.on_cmdloop_end()
            readline.set_completer(old_completer)
        return rc

    def execute(self, raw, ctx=None):
        if not ctx:
            ctx = StatementContext()

        tokens = self.preprocess(raw, 'input')
        if not tokens:
            return 0

        statement = None

        try:
            statement = self.parser.build(tokens, ctx)
        except StatementSyntaxError as e:
            self.error(self.shell_name, ": ", str(e), '\n')
            return 1

        rc = None
        if statement:
            (params, op) = statement.next()
            while params:
                cmd = None
                if params.name in self.commands:
                    cmd = self.commands[params.name]
                elif self.fallback_cmd:
                    cmd = self.fallback_cmd.fallback(self, params.name, params.args, statement.ctx)

                if not cmd:
                    statement.ctx.reset_io()
                    self.error(self.shell_name, ": ", params.name, ": command not found\n")
                    return 1

                statement.ctx.setup_io(cmd, params, op)
                rc = self.run_cmd(cmd, params, statement.ctx)
                if op == '||':
                    if rc == 0:
                        statement.ctx.reset_io()
                        return 0
                elif op == '&&' or op == '|':
                    if rc != 0:
                        statement.ctx.reset_io()
                        return rc

                (params, op) = statement.next()

        statement.ctx.reset_io()

        for pp in self.postprocessors:
            pp.on_statement_finished(self)

        return rc

    def run_cmd(self, cmd, params, ctx):
        self.errno = cmd.run(self, params.args, ctx)
        return self.errno

    def preprocess(self, raw, origin):
        for pp in self.preprocessors:
            raw = pp.on_input(self, raw)
            if raw is None:
                return None

        tokens = self.parser.tokenize(raw)
        for pp in self.preprocessors:
            tokens = pp.on_tokenize(self, tokens, origin)
            if tokens is None:
                break

        return tokens

    def preprocess_single(self, raw, origin):
        tokens = [StringToken(0, raw, quote='"')]
        for pp in self.preprocessors:
            tokens = pp.on_tokenize(self, tokens, origin)
            if not tokens:
                break

        if tokens:
            self.parser.clean_escapes(tokens)
            ret = ''
            for token in tokens:
                ret += token.text
            return ret
        return ''

    def get_completions(self, line, prefix):
        tokens = self.parser.tokenize(line)
        cmd_name = None
        loc = None
        args = []
        next_arg = True
        prev = None
        ret = []
        for token in tokens:
            if isinstance(token, StringToken):
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
                if token.operator in ('|', ';', '&&', '||'):
                    cmd_name = None
                    args = []
                    next_arg = True
                elif token.operator in ('>', '<', '>>'):
                    loc = 'path'
                    args = []
            elif isinstance(token, WhitespaceToken):
                if loc == 'name':
                    loc = None
                next_arg = True
            prev = token

        if loc == 'path':
            ret = path_completer(self, args, prefix)
        elif not cmd_name or loc == 'name':
            ret = [cmd for cmd in self.commands if cmd.startswith(prefix)]
        else:
            if cmd_name not in self.commands:
                ret = []
            else:
                if next_arg:
                    args.append('')

                cmd = self.commands[cmd_name]
                ret = cmd.complete(self, args, prefix)
        return ret

    def complete(self, text, state):
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
