
import os

class GuiTheme(object):
    # comment
    def __init__(self, path):
        p = os.path.join(path, "widgets.css")
        self.widgets = open(p, 'r').read()

        p = os.path.join(path, "term.css")
        self.term = open(p, 'r').read()

    @classmethod
    def from_builtin(self, name):
        return GuiTheme(
            os.path.join(
                os.path.dirname(__file__),
                "themes",
                name
            )
        )
