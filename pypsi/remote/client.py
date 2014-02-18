
from pypsi.remote.session import RemotePypsiSession, RemoteEOFError
import socket
import readline


class ShellClient(RemotePypsiSession):

    def __init__(self, host, port):
        super(ShellClient, self).__init__()
        self.host = host
        self.port = port
        self.running = False
        self.completions = None

    def complete(self, text, state):
        if state == 0:
            self.completions = []
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            line = readline.get_line_buffer()
            prefix = line[begidx:endidx] if line else ''
            line = line[:endidx]

            try:
                self.send_json({
                    'complete': True,
                    'line': line,
                    'prefix': prefix
                })
            except RemoteEOFError:
                raise EOFError

            try:
                obj = self.recv_json()
            except RemoteEOFError:
                raise EOFError
            else:
                if 'completions' in obj:
                    self.completions = obj['completions']
        return self.completions[state] if state < len(self.completions) else None


    def run(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)
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
