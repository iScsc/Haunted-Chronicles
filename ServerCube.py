
# ----------------------- Imports -----------------------

import socketserver
import socket
from random import randint

# ----------------------- IP -----------------------

def extractingIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    IP = s.getsockname()[0]
    s.close()
    return(IP)


# ----------------------- Constants-----------------------
sizeX = 1000
sizeY = 1000
size = (sizeX,sizeY)

stepX = 15
stepY = 15

IP = extractingIP()

SizeMaxPseudo = 10 


# ----------------------- Variables -----------------------
dicoJoueur = {} # format : x,y,color,dx,dy



# -------------------- Processing a Request -----------------------
def processRequest(s):
    type = typeOfRequest(s)
    if type == "CONNECT":
        return(processConnect(s))
    elif type == "INPUT":
        return(processInput(s))
    elif type == "DISCONNECTION":
        return(processDisconection(s))
    else :
        return("Invalid Request")

def processConnect(s):
    pseudo = extractPseudo(s)
    if validPseudo(pseudo):
        return("This Pseudo already exists")
    elif len(pseudo)>SizeMaxPseudo:
        return("Your pseudo is too big !")
    elif " " in pseudo:
        return("Don't use ' ' in your pseudo")
    else :
        initNewPlayer(pseudo)
        return(firstConnection(pseudo))
    
def processInput(s):
    pseudo = extractPseudo(s)
    if not(validPseudo(pseudo)):
        return("No player of that name")
    inputLetter = extractLetter(s,pseudo)
    Rules(inputLetter,pseudo)
    return(states())

def processDisconection(s):
    pseudo = extractPseudo(s)
    dicoJoueur.pop(pseudo)
    return("DISCONNECTED" + s[13:])


def typeOfRequest(s):
    type = ""
    i = 0
    n = len(s)
    while i<n and s[i]!=" ":
        type+=s[i]
        i+=1
    return(type)

def extractPseudo(s):
    pseudo = ""
    n = len(s)
    i0 = len(typeOfRequest(s)) + 1
    i = i0
    while i<n and s[i]!=" ":
        pseudo+=s[i]
        i+=1
    return(pseudo)

def extractLetter(s,pseudo):
    n = len(pseudo)
    return(s[7 + n])


def states():
    liste = []
    for key in dicoJoueur:
        x,y,color,dx,dy = dicoJoueur[key]
        liste.append((key,color,(x,y),(dx,dy))) 
    out = "STATE "+(str(liste)).replace(" ","")+" END"
    return(out)
    
def firstConnection(pseudo):
    out = "CONNECTED "+pseudo+" "+(str(size)).replace(" ","")+" "+states()
    return(out)

def validPseudo(pseudo):
    return(pseudo in dicoJoueur.keys())


# ----------------------- Games Rules -----------------------

def Rules(inputLetter,pseudo):
    x,y,color,dx,dy = dicoJoueur[pseudo]

    match inputLetter:
        case ".": #nothing
            #x+=randint(-1,1)
            #y+=randint(-1,1)
            pass
        case "R":
            x+=stepX
        case "L":
            x-=stepX
        case "U":
            y-=stepY
        case "D":
            y+=stepY
        case "T":
            x,y = positionNewPlayer()
        case _ :
            return("Invalid Input")
    if correctPosition(x,y,dx,dy):
        dicoJoueur[pseudo] = x,y,color,dx,dy
    return()

def correctPosition(x,y,dx,dy):
    correctX = (x>=0) and (x+dx <= sizeX)
    correctY = (y>=0) and (y+dy <= sizeY)
    return correctX and correctY
    


# ----------------------- Init of a new Player -----------------------


def initNewPlayer(pseudo):
    x,y = positionNewPlayer()
    color = colorNewPlayer()
    dx,dy = sizeNewPlayer()
    dicoJoueur[pseudo] = [x,y,color,dx,dy]
    
def positionNewPlayer():
    return(sizeX/2,sizeY/2)

def colorNewPlayer():
    return((randint(1,255),randint(1,255),randint(1,255)))
    
def sizeNewPlayer():
    return(sizeX/10,sizeY/10)
        


# ----------------------- Handler -----------------------

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
        in_data = str(self.data,'utf-16')
        print(in_data)
        
        out = processRequest(in_data)
        print(">>> ",out,"\n")
        self.request.sendall(bytes(out,'utf-16'))



# ----------------------- Main -----------------------

if __name__ == "__main__":
    HOST, PORT = str(IP), 9998
    #HOST, PORT = "localhost", 9998
    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        print("HOST = ",IP,"\nPORT = ",PORT,"\n")
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()









