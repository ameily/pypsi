from typing import Dict, Any
import threading


class ThreadLocalProxy:

    def __init__(self, target: Any):
        self._target = target
        self._proxies: Dict[int, Any] = {}

    def thread_local_proxy(self, proxy: Any, thread_id: int = None) -> None:
        if thread_id is None:
            thread_id = threading.get_ident()
        self._proxies[thread_id] = proxy or self._target

    def thread_local_unproxy(self, thread_id: int = None) -> None:
        if thread_id is None:
            thread_id = threading.get_ident()
        self._proxies.pop(thread_id, None)

    def thread_local_get(self, thread_id: int = None) -> Any:
        if thread_id is None:
            thread_id = threading.get_ident()
        return self._proxies.get(thread_id, self._target)

    def __getattr__(self, name: str) -> Any:
        target = self._proxies.get(threading.get_ident(), self._target)
        return getattr(target, name)
