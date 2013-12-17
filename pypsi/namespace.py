

class Namespace(object):

    def __init__(self, _name, **kwargs):
        self._name = _name
        self._locals = kwargs or {}

    def __getattr__(self, name):
        if not name:
            raise AttributeError(name)

        if name in self._locals:
            return self._locals[name]

        raise AttributeError(name)

    def __contains__(self, name):
        return name in self._locals

    def __iter__(self):
        return iter(self._locals)

    def __getitem__(self, name):
        if name in self._locals:
            return self._locals[name]

        raise KeyError(name)

    def __setitem__(self, name, value):
        self._locals[name] = value
