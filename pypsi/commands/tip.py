
from pypsi.base import Command, PypsiArgParser
from pypsi.stream import AnsiStdout
from pypsi.format import word_wrap
from pypsi.utils import safe_open
import random

class TipCommand(Command):

    def __init__(self, name='tip', brief='print shell tips', topic='shell', tips=None, motd=None, **kwargs):
        self.tips = tips or []
        self.motd = motd or ''
        self.rand = random.Random()
        self.rand.seed()

        self.parser = PypsiArgParser(
            prog=name,
            description=brief
        )

        self.parser.add_argument(
            '-m', '--motd', action='store_true', help="print the message of the day"
        )

        super(TipCommand, self).__init__(
            name=name, brief=brief, topic=topic,
            usage=self.parser.format_help(), **kwargs
        )

    def load_tips(self, path):
        fp = safe_open(path, 'r')
        tip = []
        for line in fp.readlines():
            line = line.rstrip()
            if line:
                tip.append(line)
            elif tip:
                self.tips.append(''.join(tip))
                tip = []
        if tip:
            self.tips.append(''.join(tip))
        fp.close()

    def load_motd(self, path):
        fp = safe_open(path, 'r')
        self.motd = fp.read().rstrip()
        fp.close()

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(shell, args)
        if self.parser.rc is not None:
            return self.parser.rc

        if ns.motd:
            self.print_motd(shell)
        else:
            self.print_random_tip(shell)

        return 0

    def print_random_tip(self, shell, header=True):
        i = int(self.rand.random() * 10) % len(self.tips)
        
        if header:
            title = "Tip #{}".format(i+1)
            title += '\n' + ('-'*len(title))
            print(AnsiStdout.green, title, AnsiStdout.reset)

        print(word_wrap(self.tips[i], shell.width))

    def print_motd(self, shell):
        print(
            AnsiStdout.green,
            "Message of the Day".center(shell.width), '\n',
            '>' * shell.width, "\n",
            AnsiStdout.reset,
            word_wrap(self.motd, shell.width), '\n',
            AnsiStdout.green,
            "<" * shell.width, "\n",
            AnsiStdout.reset,
            sep=''
        )
