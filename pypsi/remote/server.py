
import threading
import sys
import json
from io import StringIO
import select
import socket
from pypsi.remote.session import RemotePypsiSession, ConnectionClosed
from pypsi.remote import protocol as proto
import builtins

def server_print(*msg):
    #pass
    print(file=sys.stdout._get_root(), *msg)


class ThreadProxy(object):

    def __init__(self, orig):
        self._lock = threading.Lock()
        self._root = threading.get_ident()
        self._proxies = {}
        self._register_proxy(orig)

    def _register_proxy(self, obj):
        self._lock.acquire()
        self._proxies[threading.get_ident()] = obj
        self._lock.release()
        #if obj != sys.stdout:
        #    server_print("register_proxy(", threading.get_ident(), ") =", obj)

    def _deregister_proxy(self):
        self._lock.acquire()
        if threading.get_ident() in self._proxies:
            del self._proxies[threading.get_ident()]
        self._lock.release()

    def __call__(self, *args, **kwargs):
        return self._get(threading.get_ident())(*args, **kwargs)

    def _get(self, id):
        return self._proxies[id]

    def _get_root(self):
        return self._proxies[self._root]

    def __getattr__(self, name):
        if threading.get_ident() in self._proxies:
            return getattr(self._proxies[threading.get_ident()], name)
        raise AttributeError("no proxy for current thread")

    def __setattr__(self, name, value):
        if name in ('_lock', '_root', '_proxies'):
            super(ThreadProxy, self).__setattr__(name, value)
        elif threading.get_ident() in self._proxies:
            setattr(self.proxiesp[threading.get_ident()], name, value)
        else:
            raise AttributeError("no proxy for current thread")


class SessionFileObjProxy(object):

    def __init__(self, session, isatty=True):
        self._isatty = isatty
        self._session = session
        self._buffer = StringIO()

    def __getattr__(self, name):
        return getattr(self._session.socket, name)

    def __setattr__(self, name, value):
        if name in ('_session', '_buffer', '_isatty'):
            super(SessionFileObjProxy, self).__setattr__(name, value)
        else:
            return setattr(self._session.socket, name, value)

    def write(self, s):
        #server_print("write():", s)
        self._buffer.write(s)
        c = len(s)
        if '\n' in s:
            self.flush()
        return c

    def flush(self):
        #server_print("flush:", self._buffer.tell())
        if self._buffer.tell() != 0:
            t = self._buffer.getvalue()
            try:
                self._session.sendmsg(proto.ShellOutputResponse(t))
            except ConnectionClosed:
                raise EOFError
            self._buffer = StringIO()

    def isatty(self):
        return self._isatty


class ServerWorker(threading.Thread, RemotePypsiSession):

    def __init__(self, socket, shell_ctor):
        threading.Thread.__init__(self)
        RemotePypsiSession.__init__(self, socket)
        self.running = False
        self.shell_ctor = shell_ctor
        self.fp = open('out.txt', 'w')

    def run(self):
        try:
            self.buffer = StringIO()
            self.stdout = SessionFileObjProxy(self)
            #server_print("stdout:", self.stdout)
            self.queue = []
            self.running = True
            builtins.input._register_proxy(self.input)
            sys.stdout._register_proxy(self.stdout)
            sys.stderr._register_proxy(self.stdout)
            #sys.stdin._register_proxy(self.stdin)
            self.shell = self.shell_ctor()
            self.shell.cmdloop()
        except ConnectionClosed:
            pass
        except:
            import traceback
            server_print(traceback.format_exc())

        self.cleanup()
        self.running = False

        return 0

    def flush_stdout(self):
        try:
            self.stdout.flush()
        except ConnectionClosed:
            raise EOFError

    def handle(self, msg):
        if isinstance(msg, proto.InputResponse):
            pass
        elif isinstance(msg, proto.CompletionRequest):
            pass
        else:
            pass

    def send_json(self, obj):
        self.fp.write(str(obj))
        self.fp.write('\n')
        self.fp.flush()
        return super().send_json(obj)

    def input(self, msg=''):
        self.flush_stdout()

        try:
            self.sendmsg(proto.InputRequest(msg))
        except ConnectionClosed:
            raise EOFError


        while True:
            msg = None
            try:
                msg = self.recvmsg()
            except proto.InvalidMessageError:
                return ''
            except ConnectionClosed:
                raise EOFError

            if isinstance(msg, proto.InputResponse):
                if msg.sig:
                    if msg.sig == 'int':
                        raise KeyboardInterrupt
                    elif msg.sig == 'eof':
                        raise EOFError
                return msg.input
            elif isinstance(msg, proto.CompletionRequest):
                try:
                    self.sendmsg(
                        proto.CompletionResponse(
                            self.shell.get_completions(msg.input, msg.prefix)
                        )
                    )
                except ConnectionClosed:
                    raise EOFError
            else:
                return ''

    def stop(self):
        #server_print("stopping...")
        self.running = False

    def cleanup(self):
        sys.stdout._deregister_proxy()
        sys.stderr._deregister_proxy()
        builtins.input._deregister_proxy()
        self.socket.close()
        self.fp.close()
        #server_print("ServerWorker.cleanup()")


class ShellServer(object):

    def __init__(self, port, shell_ctor):
        self.port = port
        self.shell_ctor = shell_ctor
        self.threads = []
        self.running = False
        self.clients = {}

    def run(self):
        self.running = True
        sys.stdout = ThreadProxy(sys.stdout)
        sys.stderr = sys.stdout
        builtins.input = ThreadProxy(builtins.input)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.listen(5)

        try:
            while self.running:
                if self.poll():
                    (sock, addr) = self.socket.accept()
                    print("Client connected:", addr[0])
                    self.spawn(sock, addr)
                else:
                    self.purge()
        except KeyboardInterrupt:
            self.stop()
        except:
            import traceback
            print(traceback.format_exc())
            self.stop()

        self.cleanup()
        return 0

    def poll(self):
        fd = self.socket.fileno()
        (read, write, err) = select.select([fd], [], [fd], 0.5)
        if read or err:
            return True
        return False

    def spawn(self, sock, addr):
        t = ServerWorker(sock, self.shell_ctor)
        self.threads.append(t)
        t.start()
        self.clients[t.ident] = addr
        #server_print("spawn:", t.ident, "(", threading.get_ident(), ")")

    def cleanup(self):
        #print("ShellServer.cleanup()")
        for t in self.threads:
            t.stop()

        for t in self.threads:
            t.join()

        self.threads = []

    def stop(self):
        #server_print("ShellServer.stop()")
        self.running = False

    def purge(self):
        old = [t for t in self.threads if not t.is_alive()]
        for t in old:
            self.threads.remove(t)
            print("Client disconnected:", self.clients[t.ident][0])
            del self.clients[t.ident]
            #server_print("purging:", t.ident)
            del t

