

class Namespace(object):

    def __init__(self, **kwargs):
        for (k, v) in kwargs.iteritems():
            super(Namespace, self).__setattr__(k, v)

    def __setattr__(self, name, value):
        super(Namespace, self).__setattr__(name, value)

    def __iter__(self):
        return iter(self.__dict__)

    def __getitem__(self, name):
        return super(Namespace, self).__getattribute__(name)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    def __delitem__(self, name):
        self.__delattr__(self, name)

    def __delattr__(self, name):
        super(Namespace, self).__delattr__(name)


class ScopedNamespaceContext(object):

    def __init__(self, name, case_sensitive, locals, parent):
        self.name = name
        self.case_sensitive = case_sensitive
        self.locals = locals
        self.parent = parent


class ScopedNamespace(object):

    def __init__(self, name, case_sensitive=True, locals=None, parent=None):
        ctx = ScopedNamespaceContext(
            name=name,
            case_sensitive=case_sensitive,
            locals={},
            parent=parent
        )

        for (k, v) in locals.iteritems():
            if not case_sensitive:
                k = k.lower()
            ctx.locals[k] = v
        self._ctx = ctx

    def __getattribute__(self, name):
        if name[0] == '_':
            return super(ScopedNamespace, self).__getattribute__(name)

        ctx = super(ScopedNamespace, self).__getattribute__('_ctx')
        if not ctx.case_sensitive:
            name = name.lower()

        return ctx.locals[name]

    def __setattr__(self, name, value):
        if name[0] == '_':
            super(ScopedNamespace, self).__setattr__(name, value)
        else:
            ctx = super(ScopedNamespace, self).__getattribute__('_ctx')
            if not ctx.case_sensitive:
                name = name.lower()

            ctx.locals[name] = value

    def __getitem__(self, name):
        return self.__getattribute__(name)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    def __delattr__(self, name):
        ctx = super(ScopedNamespace, self).__getattribute__('_ctx')
        if not ctx.case_sensitive:
            name = name.lower()

        del ctx.locals[name]

    def __delitem__(self, name):
        self.__delattr__(name)

    def __contains__(self, name):
        ctx = super(ScopedNamespace, self).__getattribute__('_ctx')
        if not ctx.case_sensitive:
            name = name.lower()
        return name in ctx.locals
