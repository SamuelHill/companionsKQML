
import socket
port = 7000

while 1:
	s = socket.socket()
	s.connect(("127.0.0.1", port))
	s.send(b"Hisock2")
	print(s.recv(1024))
	s.close()
