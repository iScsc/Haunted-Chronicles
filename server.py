import socketserver
import asyncio
from displayer import Displayer

class Server:
    
    def __init__(self) -> None:
        pass
    
    def listen(self):
        socketserver.TCPServer.allow_reuse_address = True
        HOST, PORT = "10.193.61.229", 9998
        
        with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
            # Activate the server; this will keep running until you
            # interrupt the program with Ctrl-C
            print("Test")
            server.serve_forever()

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print("data received !")
        self.request.sendall(self.data)
