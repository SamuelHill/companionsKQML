import io
import socket
from datetime import datetime
from dateutil.relativedelta import relativedelta
from kqml import KQMLModule, KQMLPerformative, KQMLList, KQMLReader, \
                 KQMLDispatcher


def performative(string: str) -> KQMLPerformative:
    return KQMLPerformative.from_string(string)


class Pythonian(KQMLModule):
    name = 'Pythonian'

    def __init__(self, listener_port=8950, **kwargs):
        self.listener_port = listener_port
        super().__init__(name=self.name, **kwargs)
        self.starttime = datetime.now()
        self.listen_socket = socket.socket()
        self.listen_socket.bind(('', self.listener_port))
        self.listen_socket.listen(10)
        self.start()
        # self.listen()

    def register(self):
        perf_string = f'(register :sender {self.name} :receiver facilitator)'
        perf = performative(perf_string)
        socket_url = f'"socket://{self.host}:{self.listener_port}"'
        perf.set('content',
                 KQMLList([socket_url, 'nil', 'nil', self.listener_port]))
        self.send(perf)

    def receive_tell(self, msg, content):
        print(msg)
        print(content)

    def receive_eof(self):
        connection, _ = self.listen_socket.accept()
        print(connection)
        # socket_write = socket.SocketIO(connection, 'w')
        # self.out = io.BufferedWriter(socket_write)
        socket_read = socket.SocketIO(connection, 'r')
        inp_reader = KQMLReader(io.BufferedReader(socket_read))
        # self.inp = inp_reader
        self.dispatcher = KQMLDispatcher(self, inp_reader, self.name)
        self.dispatcher.start()

    # def listen(self):
    #     while True:
    #         connection, _ = self.listen_socket.accept()
    #         print(connection)
    #         socket_write = socket.SocketIO(connection, 'w')
    #         self.out = io.BufferedWriter(socket_write)
    #         socket_read = socket.SocketIO(connection, 'r')
    #         inp_reader = KQMLReader(io.BufferedReader(socket_read))
    #         # self.inp = inp_reader
    #         self.dispatcher = KQMLDispatcher(self, inp_reader, self.name)
    #         self.dispatcher.start()

    def receive_other_performative(self, msg):
        if msg.head() == 'ping':
            update_string = (
                f'(update :sender {self.name} :content (:agent {self.name} '
                f':uptime {self._uptime()} :status :OK :state idle '
                f':machine {socket.gethostname()}))'
            )
            self.reply(msg, performative(update_string))
        else:
            self.error_reply(msg, 'unexpected performative: ' + str(msg))

    def _uptime(self):
        time_list = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
        diff = relativedelta(datetime.now(), self.starttime)
        time_diffs = [getattr(diff, time) for time in time_list]
        return f'({" ".join(map(str, time_diffs))})'


if __name__ == '__main__':
    Pythonian(port=9000)
