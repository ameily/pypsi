
from pypsi.base import Plugin, Preprocessor
from pypsi.cmdline import StringToken


class MultilinePlugin(Plugin, Preprocessor):

    def __init__(self, prompt='> ', **kwargs):
        super(MultilinePlugin, self).__init__(**kwargs)
        self.prompt = prompt
        self.orig_prompt = None
        self.buffer = None

    def setup(self, shell):
        pass

    def set_ml_prompt(self, shell):
        self.orig_prompt = shell.prompt
        shell.prompt = self.prompt

    def reset_prompt(self, shell):
        if self.orig_prompt:
            shell.prompt = self.orig_prompt
            self.orig_prompt = ''

    def on_tokenize(self, shell, tokens):
        if not tokens:
            if self.buffer:
                self.reset_prompt(shell)
                ret = self.buffer
                self.buffer = None
                return ret
            else:
                return tokens

        if not isinstance(tokens[-1], StringToken):
            return self.buffer + tokens if self.buffer else tokens

        last = tokens[-1]
        escape = False
        for i in range(len(last.text)-1, -1, -1):
            c = last.text[i]
            if c != '\\':
                break
            else:
                escape = not escape

        if escape:
            last.text = last.text[:-1] # remove last \\
            if self.buffer:
                self.buffer.extend(tokens)
            else:
                self.set_ml_prompt(shell)
                self.buffer = tokens

            tokens = []
        elif self.buffer:
            tokens = self.buffer + tokens
            self.buffer = None
            self.reset_prompt(shell)

        return tokens

    def on_input_canceled(self, shell):
        self.reset_prompt(shell)
        self.buffer = None
