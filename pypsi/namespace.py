

class Namespace(object):

    def __init__(self, _name, _case_sensitive=True, **kwargs):
        self._name = _name
        self._case_sensitive = _case_sensitive
        self._locals = kwargs or {}

    def __getattr__(self, name):
        if not self._case_sensitive:
            name = name.lower()

        if not name:
            raise AttributeError(name)

        if name in self._locals:
            return self._locals[name]

        raise AttributeError(name)

    def __contains__(self, name):
        if not self._case_sensitive:
            name = name.lower()

        return name in self._locals

    def __iter__(self):
        return iter(self._locals)

    def __getitem__(self, name):
        if not self._case_sensitive:
            name = name.lower()

        if name in self._locals:
            return self._locals[name]

        raise KeyError(name)

    def __setitem__(self, name, value):
        if not self._case_sensitive:
            name = name.lower()

        self._locals[name] = value
