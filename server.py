
# ----------------------- Imports -----------------------


from socket import *
from random import randint

from threading import *
import time

from player import Player
from wall import Wall
from light import Light
from inlight import *
from common import *

# ----------------------- IP -----------------------

def extractingIP():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return(ip)


# ----------------------- Constants-----------------------
DEBUG=False

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

# Maybe not mandatory
WAITING_TIME = 0.0001 # in seconds - period of connection requests when trying to connect to the host

HOST = str(IP)
PORT = 9998

MAINSOCKET = None
LOCK = None
BACKLOG = 1


LISTENING = True
MANAGING = True
STOP = False

# ----------------------- Variables -----------------------
dicoJoueur = {} # Store players' Player structure

dicoSocket = {} # Store clients' (sock, addr) structures where sock is the socket used for communicating, and addr = (ip, port)
waitingDisconnectionList = []

dicoMur = {}

dicoMur[-1] = Wall(-1, Color(50, 50, 50), Position(350, 575), Size(225, 10))
dicoMur[0] = Wall(0, Color(50, 50, 50), Position(150, 800), Size(200, 10))
dicoMur[1] = Wall(1, Color(50, 50, 50), Position(350, 500), Size(10, 310))
dicoMur[2] = Wall(2, Color(50, 50, 50), Position(250, 500), Size(100, 10))

dicoMur[3] = Wall(3, Color(30, 30, 30), Position(850, 100), Size(10, 450))
dicoMur[4] = Wall(4, Color(30, 30, 30), Position(450, 100), Size(400, 10))

dicoMur[5] = Wall(5, Color(30, 30, 30), Position(75, 100), Size(275, 10))
dicoMur[6] = Wall(6, Color(30, 30, 30), Position(75, 50), Size(10, 200))

dicoMur[7] = Wall(7, Color(30, 30, 30), Position(325, 250), Size(150, 10))

dicoMur[8] = Wall(8, Color(30, 30, 30), Position(850, 650), Size(10, 250))
dicoMur[9] = Wall(9, Color(30, 30, 30), Position(650, 800), Size(550, 10))
#dicoMur[10] = Wall(10, Color(30, 30, 30), Position(850, 950), Size(10, 250))

dicoMur[11] = Wall(11, Color(30, 30, 30), Position(1400, 800), Size(200, 10))
dicoMur[12] = Wall(12, Color(30, 30, 30), Position(1600, 300), Size(10, 510))
dicoMur[13] = Wall(13, Color(30, 30, 30), Position(1400, 225), Size(200, 10))
dicoMur[14] = Wall(14, Color(30, 30, 30), Position(1400, 225), Size(10, 510))

dicoMur[15] = Wall(15, Color(30, 30, 30), Position(1400, 625), Size(150, 10))
dicoMur[16] = Wall(16, Color(30, 30, 30), Position(1450, 400), Size(150, 10))

dicoMur[17] = Wall(17, Color(30, 30, 30), Position(1150, 0), Size(10, 350))
dicoMur[18] = Wall(18, Color(30, 30, 30), Position(1000, 450), Size(310, 10))

WALLS = []
for key in dicoMur:
    WALLS.append(dicoMur[key])

def dummyLights():
    l0 = Light(Position(int(200),int(200)))
    l1 = Light(Position(int(500),int(800)))
    l2 = Light(Position(int(1500),int(500)))
    #l01 = Light(Position(int(100),int(800)))
    return([l0,l1,l2])    

t1 = time.time()
LIGHTS = dummyLights()
STATIC_SHADOW = AllSources(LIGHTS, WALLS, SIZE_X, SIZE_Y)
LIST_STATIC_SHADOW = [OneSource(l, WALLS, SIZE_X, SIZE_Y) for l in LIGHTS]
t2 = time.time()
print("time of precalculation : ",t2-t1," s")

# -------------------- Processing a Request -----------------------
def processRequest(ip, s):
    type = typeOfRequest(s)
    if type == "CONNECT":
        return(processConnect(s))
    elif type == "INPUT":
        return(processInput(ip, s))
    elif type == "DISCONNECTION":
        return(processDisconnection(ip, s))
    else :
        return("Invalid Request")

def processConnect(s):
    pseudo = extractPseudo(s)
    if validPseudo(pseudo):
        return("This Pseudo already exists")
    elif len(pseudo)>SIZE_MAX_PSEUDO:
        return("Your pseudo is too big !")
    elif " " in pseudo:
        return("Don't use ' ' in your pseudo !")
    else :
        initNewPlayer(pseudo)
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

def processDisconnection(ip, s):
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


def states(pseudo):
    player = 0
    liste = []
    listOfPlayer = []
        
    for key in dicoJoueur:
        p =  dicoJoueur[key]
        if key == pseudo:
            player = p
        listOfPlayer.append(p)
    
    shadows = Visible(player, LIGHTS, listOfPlayer, SIZE_X, SIZE_Y, STATIC_SHADOW, WALLS, LIST_STATIC_SHADOW)
    visiblePlayer = allVisiblePlayer(shadows,listOfPlayer)
    formatShadows = sendingFormat(shadows)
    
    liste.append(str(player))
    for key in visiblePlayer:
        p = dicoJoueur[key]
        if key != pseudo:       
            liste.append(str(p))

    out = "STATE "+(str(liste)).replace(" ","")+" SHADES "+formatShadows+" END"

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
    return (pseudo in dicoJoueur.keys() and pseudo in dicoSocket.keys() and dicoSocket[pseudo][1][0] == str(ip))


# ----------------------- Games Rules -----------------------

def Rules(inputLetter,pseudo):
    _, _, position1, size1 = dicoJoueur[pseudo].toList()
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
            _, _, position, size = dicoJoueur[key].toList()
            
            if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
                return True
    
    return False



# ----------------------- Init of a new Player -----------------------


def initNewPlayer(pseudo):
    dx,dy = sizeNewPlayer()
    
    x,y = positionNewPlayer(dx, dy)
    
    while not correctPosition(pseudo, x, y, dx, dy):
        x, y = positionNewPlayer(dx, dy)
    
    color = colorNewPlayer()
    dicoJoueur[pseudo] = Player(pseudo, color, Position(x,y), Size(dx,dy))

def sizeNewPlayer():
    return PLAYER_SIZE

def positionNewPlayer(dx, dy):
    return(randint(0, int(SIZE_X - dx)), randint(0, int(SIZE_Y - dy)))

def colorNewPlayer():
    return Color(randint(1,255),randint(1,255),randint(1,255))



# ----------------------- Threads -----------------------
def manage_server():
    global STOP
    global LISTENING
    global MANAGING
    
    global MAINSOCKET
    
    while not STOP:
        command = input()
        match command:
            case "stop":
                STOP = True
                print("STOP = ", STOP)
                try:
                    MAINSOCKET.shutdown(SHUT_RDWR)
                except error:
                    print("MAINSOCKET could not be shutdown")
                MAINSOCKET.close()
                
                print("Socket server closed !")
                
                for username, (sock,addr) in dicoSocket.items():
                    try:
                        sock.shutdown(SHUT_RDWR)
                    except error:
                        print("Player " + username + "'s socket could not be shutdown.")
                    sock.close()
                
                print("Client sockets closed !")
                
                print("Every sockets has been successfully closed!")
            case "deaf":
                LISTENING = False
                print("LISTENING = ", LISTENING)
            case "listen":
                LISTENING = True
                print("LISTENING = ", LISTENING)
            case "ignore":
                MANAGING = False
                print("MANAGING = ", MANAGING)
            case "manage":
                MANAGING = True
                print("MANAGING = ", MANAGING)
            case _:
                print("Wrong command : use either stop, deaf, listen, ignore, manage")
                print("STOP = ", STOP)
                print("LISTENING = ", LISTENING)
                print("MANAGING = ", MANAGING)
                
def listen_new():
    global STOP
    global LISTENING
    
    while not STOP:
        while LISTENING and not STOP:
            try:
                sock, addr = MAINSOCKET.accept()
                in_ip = addr[0]
                
                if(LISTENING):
                    try:
                        data = sock.recv(1024).strip()
                        
                        in_data = str(data,'utf-16')
                        
                        if DEBUG:
                            print("{} wrote:".format(in_ip))
                            print(in_data)
                        
                        out = processRequest(in_ip ,in_data)
                        message = out.split(' ')
                        
                        if message[0]=="CONNECTED":
                            LOCK.acquire()
                            username = message[1]
                            dicoSocket[username] = (sock, addr)
                            LOCK.release()

                        if DEBUG:
                            print(">>> ",out,"\n")
                        
                        try:
                            sock.sendall(bytes(out,'utf-16'))
                        except error:
                            print("New connection from " + str(in_ip) + " failed!")
                    except error:
                        print("New connection from " + str(in_ip) + " failed!")
                
                else:
                    print("Connection attempt from " + str(in_ip) + " | Refused : LISTENING = " + str(LISTENING))
            except error:
                print("The main socket was closed. LISTENING = " + str(LISTENING) + " and STOP = " + str(STOP))
            
            time.sleep(WAITING_TIME)
        
        time.sleep(WAITING_TIME)

def listen_old():
    global STOP
    global MANAGING
    
    global waitingDisconnectionList
    
    while not STOP:
        while MANAGING and not STOP:
            
            for elt in waitingDisconnectionList:
                username, sock, addr = elt[0], elt[1], elt[2]
                dicoSocket.pop(username)
                
                if username in dicoJoueur.keys():
                    dicoJoueur.pop(username)
                
                sock.close()
            waitingDisconnectionList = []


            LOCK.acquire()
            for username in dicoSocket:
                sock, addr = dicoSocket[username]

                try:
                    data = sock.recv(1024).strip()
                    
                    in_ip = addr[0]
                    
                    in_data = str(data,'utf-16')
                    
                    if DEBUG:
                        print("Player {} with ip {} wrote:".format(username, in_ip))
                        print(in_data)
                    
                    out = processRequest(in_ip ,in_data)
                    message = out.split(" ")
                            
                    if message[0]=="DISCONNECTED":
                        username = message[1]
                        waitingDisconnectionList.append((username, sock, addr))
                    
                    if DEBUG:
                        print(">>> ",out,"\n")
                    try:
                        sock.sendall(bytes(out,'utf-16'))
                    except error:
                        print("Loss connection while sending data with player " + username + " (ip = " + str(addr[0]) + ")")
                        waitingDisconnectionList.append((username, sock, addr))
                except error:
                    print("Loss connection while receiving data with player " + username + " (ip = " + str(addr[0]) + ")")
                    waitingDisconnectionList.append((username, sock, addr))
            LOCK.release()
            
            time.sleep(WAITING_TIME)
        
        time.sleep(WAITING_TIME)
    


# ----------------------- Main -----------------------
def main():
    global MAINSOCKET
    global LOCK
    
    # Initialization
    if MAINSOCKET == None:
        MAINSOCKET = socket(AF_INET, SOCK_STREAM)
        MAINSOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        MAINSOCKET.bind((HOST, PORT))
        MAINSOCKET.listen(BACKLOG)
    
    if LOCK == None:
        LOCK = Lock()
    
    print("Server opened with :\n    - ip = " + str(IP) + "\n    - port = " + str(PORT))
    
    listener_new = Thread(target=listen_new)
    manager_server = Thread(target=manage_server)
    listener_old = Thread(target=listen_old)
    
    listener_new.start()
    manager_server.start()
    listener_old.start()

if __name__ == "__main__":
    main()

