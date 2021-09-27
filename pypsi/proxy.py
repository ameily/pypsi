from typing import Dict, Any
import threading


class ThreadLocalProxy:

    def __init__(self, target: Any):
        self._target = target
        self._proxies: Dict[int, Any] = {}

    def thread_local_proxy(self, proxy: Any) -> None:
        self._proxies[threading.get_ident()] = proxy or self._target

    def thread_local_unproxy(self, id: int = None) -> None:
        if id is None:
            id = threading.get_ident()
        self._proxies.pop(id, None)

    def thread_local_get(self) -> Any:
        return self._proxies.get(threading.get_ident(), self._target)

    def __getattr__(self, name: str) -> Any:
        target = self._proxies.get(threading.get_ident(), self._target)
        return getattr(target, name)
