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
Generic objects to store arbitrary attributes and values.
'''

from typing import Iterator, Any, Tuple


class Namespace:

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__setitem__(key, value)

    def __getitem__(self, name: str) -> Any:
        name = str(name)
        return self.__dict__[name]

    def __setitem__(self, name: str, value: Any) -> Any:
        name = str(name)
        self.__dict__[name] = value
        return value

    def __delitem__(self, name: str) -> None:
        name = str(name)
        del self.__dict__[name]

    def __contains__(self, name: str) -> bool:
        return name in self.__dict__

    def __iter__(self, name: str) -> Iterator[Tuple[str, Any]]:
        return iter(self.__dict__.items())


class ScopedNamespace:

    def __init__(self, **kwargs):
        object.__setattr__(self, '_stack', [dict(kwargs)])

    def __get_value(self, name: str) -> Any:
        name = str(name)
        for namespace in reversed(self._stack):
            try:
                value = namespace[name]
            except KeyError:
                pass
            else:
                return value
        return None

    def __set_value(self, name: str, value: Any, global_variable: bool = False) -> None:
        name = str(name)
        if global_variable:
            self._stack[0][name] = value
        else:
            self._stack[-1][name] = value

    def __getitem__(self, name: str) -> Any:
        return self.__get_value(name)

    def __setitem__(self, name: str, value: Any) -> Any:
        self.__set_value(name, value)
        return value

    def __getattr__(self, name: str) -> Any:
        return self.__get_value(name)

    def __setattr__(self, name: str, value: Any) -> Any:
        self.__set_value(name, value)
        return value

    def __del_value(self, name: str) -> None:
        name = str(name)
        for namespace in reversed(self._stack):
            if name in namespace:
                del namespace[name]
                return

        raise AttributeError(name)

    def __delitem__(self, name: str) -> None:
        self.__del_value(name)

    def __delattr__(self, name: str) -> None:
        self.__del_value(name)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        ctx = {}
        for namespace in self._stack:
            ctx.update(namespace)
        return iter(ctx.items())

    def __contains__(self, name: str) -> bool:
        try:
            self.__get_value(name)
        except AttributeError:
            return False
        else:
            return True

    def __enter__(self) -> 'ScopedNamespace':
        self._stack.append({})
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self._stack.pop()
        return False

    def __iadd__(self, other: dict) -> 'ScopedNamespace':
        if not isinstance(other, dict):
            raise TypeError(f'expected dict object, got {type(other)}')

        self._stack[-1].update(other)
        return self
