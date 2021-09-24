from typing import Dict, Any
import threading


class ThreadLocalProxy:

    def __init__(self, target: Any):
        self.__target = target
        self.__proxies: Dict[int, Any] = {}

    def thread_local_proxy(self, proxy: Any) -> None:
        self.__proxies[threading.get_ident()] = proxy or self.__target

    def thread_local_unproxy(self, id: int = None) -> None:
        if id is None:
            id = threading.get_ident()
        self.__proxies.pop(id, None)

    def thread_local_get(self) -> Any:
        return self.__proxies.get(threading.get_ident(), self.__target)

    def __getattr__(self, name: str) -> Any:
        target = self.__proxies.get(threading.get_ident(), self.__target)
        return getattr(target, name)
