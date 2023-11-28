import socket


class TrackingClient:
    def __init__(self):
        self.sock = None

    def connect(self):
        host, port = "127.0.0.1", 25001
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def close(self):
        self.sock.close()

    def sendString(self, s):
        self.sock.sendall(s.encode("utf-8"))

    def receiveString(self):
        return self.sock.recv(1024).decode("utf-8")
