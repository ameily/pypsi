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

'''
Generic objects to store arbitrary attributes and values.
'''


class Namespace(object):
    '''
    Provides dynamic attribute storage and retrieval. Attributes can be
    retrieved and set by either attribute accesses or :class:`dict` key access.
    The following two lines of code retrieve and set the same attribute:

    - ``namespace.my_attr = 1``
    - ``namespace['my_attr'] = 1``
    '''

    def __init__(self, **kwargs):
        '''
        :param kwargs: default attributes and their values are created
        '''
        for (k, v) in kwargs.items():
            super(Namespace, self).__setattr__(k, v)

    def __setattr__(self, name, value):
        '''
        Set an attribute's value.
        '''
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
    '''
    Provides a configurable namespace for arbitrary attribute access.
    '''

    def __init__(self, name, case_sensitive=True, locals=None, parent=None):
        '''
        :param str name: the root name
        :param bool case_sensitive: determines whether attribute names are case
            sensitive
        :param dict locals: default attributes
        :param ScopedNamespace parent: the parent namespace
        '''
        ctx = ScopedNamespaceContext(
            name=name,
            case_sensitive=case_sensitive,
            locals={},
            parent=parent
        )

        if locals:
            for (k, v) in locals.items():
                if not case_sensitive:
                    k = k.lower()
                ctx.locals[k] = v
        self._ctx = ctx

    def __getattribute__(self, name):
        if not name:
            return ''

        if name[0] == '_':
            return super(ScopedNamespace, self).__getattribute__(name)

        ctx = super(ScopedNamespace, self).__getattribute__('_ctx')
        if not ctx.case_sensitive:
            name = name.lower()

        return ctx.locals[name] if name in ctx.locals else ''

    def __setattr__(self, name, value):
        if not name:
            return -1
        
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

    def __iter__(self):
        return iter(self._ctx.locals)
