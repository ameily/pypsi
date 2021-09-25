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


'''
This is an example Pypsi shell using several key features of the Pypsi API and
architecture. The code is provided as an example of the overarching Pypsi design
and API. The demo shell can be used as a skeleton for new shells and can be
easily modified.
'''

from pypsi.shell import Shell
from pypsi.core import Command
from pypsi.plugins.cmd import CmdPlugin
from pypsi.plugins.block import BlockPlugin
from pypsi.plugins.hexcode import HexCodePlugin
from pypsi.commands.macro import MacroCommand
from pypsi.commands.system import SystemCommand
from pypsi.plugins.multiline import MultilinePlugin
from pypsi.commands.xargs import XArgsCommand
from pypsi.commands.exit import ExitCommand
from pypsi.plugins.variable import VariablePlugin
from pypsi.plugins.history import HistoryPlugin
from pypsi.plugins.alias import AliasPlugin
from pypsi.commands.echo import EchoCommand
from pypsi.commands.include import IncludeCommand
from pypsi.commands.help import HelpCommand, Topic
from pypsi.commands.tip import TipCommand
from pypsi.commands.tail import TailCommand
from pypsi.commands.chdir import ChdirCommand
from pypsi.commands.pwd import PwdCommand
from pypsi.plugins.comment import CommentPlugin

from pypsi import wizard as wiz
from pypsi.format import Table, Column
from pypsi.completers import path_completer


from pypsi.ansi import Color, ansi_clear_screen

from pypsi.os import find_bins_in_path

import sys

ShellTopic = """These commands are built into the Pypsi shell (all glory and honor to the pypsi shell).
This is a single newline

and This is a double"""



class WizardCommand(Command):
    '''
    Simple command to launch an example configuration wizard.
    '''

    def __init__(self, name='wizard', **kwargs):
        super().__init__(name=name, **kwargs)

    def run(self, shell, args):
        ns = ConfigWizard.run(shell)
        if ns:
            print()
            # Create a table with optimally sized columns.
            Table(
                columns=(
                    # FIrst column is the configuration ID. This column will be
                    # the minimum width possible without wrapping
                    Column('Config ID', Column.Shrink),
                    # Second column is the configuration value. This column will
                    # grow to a maximum width possible.
                    Column('Config Value', Column.Grow)
                ),
                # Number of spaces between each column.
                spacing=4
            ).extend(
                # Each tuple is a row
                ('ip_addr', ns.ip_addr),
                ('port', ns.port),
                ('path', ns.path),
                ('mode', ns.mode)
            ).write(sys.stdout) # Write the table to stdout
        else:
            pass

        return 0

ConfigWizard = wiz.PromptWizard(
    name="Example Configuration",
    description="Shows various examples of wizard steps",
    steps=(
        # The list of input prompts to ask the user.
        wiz.WizardStep(
            # ID where the value will be stored
            id="ip_addr",
            # Display name
            name="IP Address",
            # Help message
            help="Local IP Address or Host name",
            # List of validators to run on the input
            validators=(wiz.required_validator, wiz.hostname_or_ip_validator)
        ),
        wiz.WizardStep(
            id='port',
            name="TCP Port",
            help="TCP port to listen on",
            validators=(wiz.required_validator, wiz.int_validator(1024, 65535)),
            default=1337
        ),
        wiz.WizardStep(
            id='path',
            name='File path',
            help='File path to log file',
            validators=wiz.file_validator,
            # Tab complete based on path
            completer=path_completer
        ),
        wiz.WizardStep(
            id='mode',
            name='Shell mode',
            help='Mode of the shell',
            default='local',
            validators=(wiz.required_validator, wiz.choice_validator(['local', 'remote']))
        )
    )
)


class DemoShell(Shell):
    '''
    Example demonstration shell.
    '''

    # First, add commands and plugins to the shell
    wizard_cmd = WizardCommand()
    echo_cmd = EchoCommand()
    block_plugin = BlockPlugin()
    hexcode_plugin = HexCodePlugin()
    macro_cmd = MacroCommand()

    # Drop commands to cmd.exe if the platform is Windows
    system_cmd = SystemCommand(use_shell=(sys.platform == 'win32'))
    ml_plugin = MultilinePlugin()
    xargs_cmd = XArgsCommand()
    exit_cmd = ExitCommand()
    history_plugin = HistoryPlugin()
    include_cmd = IncludeCommand()
    cmd_plugin = CmdPlugin(cmd_args=1)
    tip_cmd = TipCommand()
    tail_cmd = TailCommand()
    help_cmd = HelpCommand()
    var_plugin = VariablePlugin(case_sensitive=False, env=False)
    comment_plugin = CommentPlugin()
    chdir_cmd = ChdirCommand()
    pwd_cmd = PwdCommand()
    alias_plugin = AliasPlugin()

    def __init__(self):
        # You must call the Shell.__init__() method.
        super().__init__()

        try:
            # Attempt to load tips
            self.tip_cmd.load_tips("./demo-tips.txt")
        except:
            self.error("failed to load tips file: demo-tips.txt")

        try:
            # Attempt to load the message of the day (MOTD)
            self.tip_cmd.load_motd("./demo-motd.txt")
        except:
            self.error("failed to load message of the day file: demo-motd.txt")

        self.prompt = (f'{Color.gray.prompt}[$time] {Color.bright_cyan.prompt}pypsi '
                       f'{Color.bright_green.prompt})> {Color.reset_all.prompt}')

        self.fallback_cmd = self.system_cmd

        # Register the shell topic for the help command
        self.help_cmd.add_topic(self, Topic("shell", "Builtin Shell Commands"))
        # Add the I/O redirection topic
        # self.help_cmd.add_topic(self, topics.IoRedirection)

        self._sys_bins = None

    def on_cmdloop_begin(self):
        ansi_clear_screen()
        if self.tip_cmd.motd:
            self.tip_cmd.print_motd(self)
            print()
        else:
            print("No tips registered. Create the demo-tips.txt file for the tip of the day.")

        if self.tip_cmd.tips:
            width = getattr(sys.stdout, 'width', 60)
            print(Color.bright_green("Tip of the Day".center(width)))
            print(Color.bright_green('>' * width))
            self.tip_cmd.print_random_tip(self, False)
            print(Color.bright_green('<' * width))
            print()
        else:
            print("To see the message of the day. Create the demo-motd.txt file for the MOTD.")

    ############################################################################
    # This functions demonstrate that existing Python :mod:`cmd` shell commands
    # work without modification in Pypsi.
    ############################################################################
    def do_cmddoc(self, args):
        '''
        This is some long description for the cmdargs command.
        '''
        print("do_cmdargs(", args, ")")
        return 0

    def help_cmdout(self):
        print("this is the help message for the cmdout command")

    def do_cmdout(self, args):
        print("do_cmdout(", args, ")")
        return 0

    def get_command_name_completions(self, prefix):
        if not self._sys_bins:
            self._sys_bins = find_bins_in_path()

        return sorted(
            [name for name in self.commands if name.startswith(prefix)] +
            [name for name in self._sys_bins if name.startswith(prefix)]
        )


if __name__ == '__main__':
    shell = DemoShell()
    rc = shell.cmdloop()
    sys.exit(rc)
