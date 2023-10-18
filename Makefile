
SERVER = 10.193.49.95
PORT = 9998

server :
	python3 ServerCube.py 

client :
	python3 client.py $(SERVER) $(PORT)







