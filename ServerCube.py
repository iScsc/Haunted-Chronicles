
# ----------------------- Imports -----------------------

import socketserver
import socket
from random import randint

from player import Player

from light import Light
from inlight import *
from wall import Wall
from common import *

# ----------------------- IP -----------------------

def extractingIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    IP = s.getsockname()[0]
    s.close()
    return(IP)


# ----------------------- Constants-----------------------

# Game map
SIZE_X = int(1920 * .9)
SIZE_Y = int(1080 * .9)
SIZE = (SIZE_X,SIZE_Y)

STEP_X = 3
STEP_Y = 3

# Server
IP = extractingIP()

# Player
SIZE_MAX_PSEUDO = 10

PLAYER_SIZE = (20, 20)

# ----------------------- Variables -----------------------
dicoJoueur = {} # Store players' Player structure

dicoMur = {}

dicoMur[-1] = Wall(-1, Color(50, 50, 50), Position(350, 575), Size(225, 10))
#dicoMur[0] = Wall(0, Color(50, 50, 50), Position(150, 800), Size(200, 10))
#dicoMur[1] = Wall(1, Color(50, 50, 50), Position(350, 500), Size(10, 310))
#dicoMur[2] = Wall(2, Color(50, 50, 50), Position(250, 500), Size(100, 10))

# dicoMur[3] = Wall(3, Color(30, 30, 30), Position(850, 100), Size(10, 450))
# dicoMur[4] = Wall(4, Color(30, 30, 30), Position(450, 100), Size(400, 10))

# dicoMur[5] = Wall(5, Color(30, 30, 30), Position(75, 100), Size(275, 10))
# dicoMur[6] = Wall(6, Color(30, 30, 30), Position(75, 50), Size(10, 200))

# dicoMur[7] = Wall(7, Color(30, 30, 30), Position(325, 250), Size(150, 10))

# dicoMur[8] = Wall(8, Color(30, 30, 30), Position(850, 650), Size(10, 250))
# dicoMur[9] = Wall(9, Color(30, 30, 30), Position(650, 800), Size(550, 10))
# dicoMur[10] = Wall(10, Color(30, 30, 30), Position(850, 950), Size(10, 250))

# dicoMur[11] = Wall(11, Color(30, 30, 30), Position(1400, 800), Size(200, 10))
# dicoMur[12] = Wall(12, Color(30, 30, 30), Position(1600, 300), Size(10, 510))
# dicoMur[13] = Wall(13, Color(30, 30, 30), Position(1400, 225), Size(200, 10))
# dicoMur[14] = Wall(14, Color(30, 30, 30), Position(1400, 225), Size(10, 510))

# dicoMur[15] = Wall(15, Color(30, 30, 30), Position(1400, 625), Size(150, 10))
# dicoMur[16] = Wall(16, Color(30, 30, 30), Position(1450, 400), Size(150, 10))

# dicoMur[17] = Wall(17, Color(30, 30, 30), Position(1150, 0), Size(10, 350))
# dicoMur[18] = Wall(18, Color(30, 30, 30), Position(1000, 450), Size(310, 10))

# -------------------- Processing a Request -----------------------
def processRequest(ip, s):
    type = typeOfRequest(s)
    if type == "CONNECT":
        return(processConnect(ip, s))
    elif type == "INPUT":
        return(processInput(ip, s))
    elif type == "DISCONNECTION":
        return(processDisconection(ip, s))
    else :
        return("Invalid Request")

def processConnect(ip, s):
    pseudo = extractPseudo(s)
    if validPseudo(pseudo):
        return("This Pseudo already exists")
    elif len(pseudo)>SIZE_MAX_PSEUDO:
        return("Your pseudo is too big !")
    elif " " in pseudo:
        return("Don't use ' ' in your pseudo !")
    else :
        initNewPlayer(ip, pseudo)
        return(firstConnection(pseudo))
    
def processInput(ip, s):
    pseudo = extractPseudo(s)
    if not(validPseudo(pseudo)):
        return("No player of that name")
    if not(validIp(ip, pseudo)):
        return("You are impersonating someone else !")
    inputLetter = extractLetter(s,pseudo)
    Rules(inputLetter,pseudo)
    return(states(pseudo))

def processDisconection(ip, s):
    pseudo = extractPseudo(s)
    if not(validIp(ip, pseudo)):
        return("You are impersonating someone else !")
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


def dummyLights():
    l00 = Light(Position(int(SIZE_X/2),int(SIZE_Y/2)))
    print(l00.position)
    #l10 = Light((SIZE_X,0))
    #l11 = Light((SIZE_X,SIZE_Y))
    #l01 = Light((0,SIZE_Y))
    return([l00])#,l10,l11,l01])    

def states(pseudo):
    player = 0
    liste = []
    listeOfPlayer = []
    listeOfWall = []
    listOfLight = dummyLights()
    
    for key in dicoJoueur:
        p =  dicoJoueur[key]
        if key == pseudo:
            player = p
        listeOfPlayer.append(p)
    
    
    for key in dicoMur:
        listeOfWall.append(dicoMur[key])
    
    shadows = Visible(player,listOfLight,listeOfPlayer+listeOfWall,SIZE_X,SIZE_Y)
    visiblePlayer = allVisiblePlayer(shadows,listeOfPlayer)
    formatshadows = sendingFormat(shadows)
    
    liste.append(str(player))
    for key in visiblePlayer:
        p = dicoJoueur[key]
        if key != pseudo:       
            liste.append(str(p))
    out = "STATE "+(str(liste)).replace(" ","")+" SHADES "+formatshadows+" END"

    return(out)

def walls():
    liste = []
    for key in dicoMur:
        liste.append(str(dicoMur[key]))
    out = "WALLS " + (str(liste)).replace(" ","") + " END"
    return(out)

def firstConnection(pseudo):

    out = "CONNECTED " + pseudo + " " + (str(SIZE)).replace(" ","") + " " + walls().replace("END","") + states(pseudo)
    return(out)

def validPseudo(pseudo):
    return(pseudo in dicoJoueur.keys())

def validIp(ip, pseudo):
    return (pseudo in dicoJoueur.keys() and dicoJoueur[pseudo].ip == ip)


# ----------------------- Games Rules -----------------------

def Rules(inputLetter,pseudo):
    _, _, _, position1, size1 = dicoJoueur[pseudo].toList()
    x,y=position1.x,position1.y

    match inputLetter:
        case ".": #nothing
            #x+=randint(-1,1)
            #y+=randint(-1,1)
            pass
        case "R":
            x+=STEP_X
        case "L":
            x-=STEP_X
        case "U":
            y-=STEP_Y
        case "D":
            y+=STEP_Y
        case "T":
            x,y = positionNewPlayer()
        case _ :
            return("Invalid Input")
    if correctPosition(pseudo, x,y,size1.w,size1.h):
        dicoJoueur[pseudo].update(position=Position(x, y), size=Size(size1.w, size1.h))
    return()

def correctPosition(pseudo, x,y,dx,dy):
    correctX = (x>=0) and (x+dx <= SIZE_X)
    correctY = (y>=0) and (y+dy <= SIZE_Y)
    
    return correctX and correctY and not collision(pseudo, x, y, dx, dy)

def collision(pseudo, x, y ,dx ,dy):
    
    c = (x + dx/2, y + dy/2)
    
    for key in dicoMur.keys():
        _, _, position, size = dicoMur[key].toList()
        
        if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
            return True
    
    for key in dicoJoueur.keys():
        if key != pseudo:
            _, _, _, position, size = dicoJoueur[key].toList()
            
            if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
                return True
    
    return False



# ----------------------- Init of a new Player -----------------------


def initNewPlayer(ip, pseudo):
    dx,dy = sizeNewPlayer()
    
    x,y = positionNewPlayer(dx, dy)
    
    while not correctPosition(pseudo, x, y, dx, dy):
        x, y = positionNewPlayer(dx, dy)
    
    color = colorNewPlayer()
    dicoJoueur[pseudo] = Player(ip, pseudo, color, Position(x,y), Size(dx,dy))

def sizeNewPlayer():
    return PLAYER_SIZE

def positionNewPlayer(dx, dy):
    return(randint(0, int(SIZE_X - dx)), randint(0, int(SIZE_Y - dy)))

def colorNewPlayer():
    return Color(randint(1,255),randint(1,255),randint(1,255))



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
        
        in_ip = self.client_address[0]
        
        print("{} wrote:".format(in_ip))
        in_data = str(self.data,'utf-16')
        print(in_data)
        
        out = processRequest(in_ip ,in_data)

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