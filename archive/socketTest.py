
import socket
port = 7000

while 1:
	s = socket.socket()
	s.connect((socket.gethostname(), port))
	s.send(b"Hisock1")
	print(s.recv(1024))
	s.close()
