
from pypsi.remote.session import RemotePypsiSession, RemoteEOFError
import socket
import readline


class ShellClient(RemotePypsiSession):

    def __init__(self, host, port):
        super(ShellClient, self).__init__()
        self.host = host
        self.port = port
        self.running = False

    def run(self):
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.connect((self.host, self.port))

        while self.running:
            obj = None
            try:
                obj = self.recv_json()
            except KeyboardInterrupt:
                self.send_json({ 'sig': 'int' })
                continue
            except RemoteEOFError:
                print()
                self.socket.close()
                print("session closed")
                return 0
            except EOFError:
                self.send_json({ 'sig': 'eof' })
                continue

            stdout = obj['stdout'] if 'stdout' in obj else ''
            if 'prompt' in obj and obj['prompt']:
                response = {}
                try:
                    line = input(stdout)
                except KeyboardInterrupt:
                    response['sig'] = 'int'
                except EOFError:
                    response['sig'] = 'eof'
                else:
                    response['input'] = line

                try:
                    self.send_json(response)
                except RemoteEOFError:
                    print("session closed")
                    return 0
            else:
                print(stdout, end='')
        return 0

    def stop(self):
        self.running = False
