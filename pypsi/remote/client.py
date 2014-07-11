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

from pypsi.remote.session import RemotePypsiSession, ConnectionClosed
from pypsi.remote import protocol as proto
import socket
import readline


class ShellClient(RemotePypsiSession):

    def __init__(self, host, port):
        super(ShellClient, self).__init__()
        # self.fp = open('log.txt', 'w')
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
                self.sendmsg(proto.CompletionRequest(line, prefix))
            except ConnectionClosed:
                raise EOFError

            try:
                msg = self.recvmsg()
            except proto.InvalidMessageError:
                raise EOFError #TODO
            else:
                self.completions = msg.completions
        return self.completions[state] if state < len(self.completions) else None

    def recv_json(self, block=True):
        obj = super().recv_json(block)
        # self.fp.write(str(obj))
        # self.fp.write('\n')
        # self.fp.flush()
        #print("obj:", obj, file=self.fp)
        #print("obj:", obj)
        #print()
        return obj

    def run(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.connect((self.host, self.port))
        self.on_connect()
        while self.running:
            msg = None
            try:
                msg = self.recvmsg()
            except ConnectionClosed:
                self.socket.close()
                print("session closed")
                break

            if isinstance(msg, proto.InputRequest):
                response = proto.InputResponse('')
                try:
                    line = input(msg.prompt)
                except KeyboardInterrupt:
                    response.sig = 'int'
                except EOFError:
                    response.sig = 'eof'
                else:
                    response.input = line

                try:
                    self.sendmsg(response)
                except ConnectionClosed:
                    print("session closed")
                    self.socket.close()
                    # self.fp.flush()
                    # self.fp.close()
                    break
            elif isinstance(msg, proto.ShellOutputResponse):
                print(msg.output, end='')
            # self.fp.close()
        self.on_disconnect()
        return 0

    def stop(self):
        self.running = False

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass
