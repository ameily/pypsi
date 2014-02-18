
from io import StringIO
import json
import select
import errno


class RemoteKeyboardInterrupt(KeyboardInterrupt):
    pass


class RemoteEOFError(EOFError):
    pass


class RemotePypsiSession(object):

    def __init__(self, socket=None):
        self.socket = socket
        self.queue = []
        self.buffer = StringIO()

    def send_json(self, obj):
        #self.p("send:", obj)
        try:
            c = self.socket.sendall(json.dumps(obj).encode())
            if c:
                raise RemoteEOFError

            c = self.socket.sendall(b'\x00')
            if c:
                raise RemoteEOFError
        except OSError as e:
            if e.errno == errno.EPIPE:
                raise RemoteEOFError
            else:
                raise e

        return 0

    def poll(self):
        fd = self.socket.fileno()
        (read, write, err) = select.select([fd], [], [fd], 0.5)
        if read or err:
            return True
        return False

    def recv_json(self):
        if self.queue:
            return json.loads(self.queue.pop(0))

        while self.running:
            if self.poll():
                s = self.socket.recv(0x1000)
                #self.p(">>", s)
                if not s:
                    raise RemoteEOFError

                s = str(s, 'utf-8')
                msg = None
                delims = s.count('\x00')
                #self.p("delims:", delims)
                if delims > 0:
                    #if delims == 1:
                    #    self.p("@", s.find('\x00'))
                    msgs = s.split('\x00')
                    #self.p("msgs:", msgs)
                    if self.buffer.tell() != 0:
                        self.buffer.write(msgs.pop(0))
                        msg = self.buffer.getvalue()
                        self.buffer = StringIO()
                    else:
                        msg = msgs.pop(0)
                        #self.p("tell() == 0;", msg)

                    msgs = [m for m in msgs if m]
                    if msgs:
                        if len(msgs) > delims:
                            self.buffer.write(msgs.pop())
                            #self.p("msgs1:", msgs)
                            self.queue = msgs
                        else:
                            #self.p("msgs2:", msgs)
                            self.queue = msgs

                    #self.p("msg:", msg)
                    if msg:
                        return json.loads(msg)
                else:
                    self.buffer.write(s)

        return None
