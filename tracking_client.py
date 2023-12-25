import socket


class TrackingClient: # Класс клиента
    def __init__(self):
        self.sock = None

    def connect(self): # метод для подключения к серверу по заданным ip и port
        host, port = "127.0.0.1", 25001
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def close(self): # метод для закрытия соединения
        self.sock.close()

    def sendString(self, s): # метод для отправки сообщения
        self.sock.sendall(s.encode("utf-8"))

    def receiveString(self): # метод для принятия сообщения
        return self.sock.recv(1024).decode("utf-8")
