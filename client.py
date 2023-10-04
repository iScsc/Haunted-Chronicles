import socket
import sys

HOST, PORT = "10.193.35.85", 9990
USERNAME = "Zyno"
data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(bytes(USERNAME + " : " + data + "\n", "utf-16"))

    # Receive data from the server and shut down
    received = str(sock.recv(1024), "utf-16")

print("Sent:     {}".format(data))
print("Received: {}".format(received))