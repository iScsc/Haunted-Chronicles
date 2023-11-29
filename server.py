
# ----------------------- Imports -----------------------


from socket import *
from random import randint

from threading import *
import time
import traceback

from player import Player
from wall import Wall
from light import Light
from inlight import *
from common import *

# ----------------------- IP -----------------------

def extractingIP():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    IP = s.getsockname()[0]
    s.close()
    return(IP)


# ----------------------- Constants-----------------------
# Game map
SIZE_X = int(1920 * .9)
SIZE_Y = int(1080 * .9)
SIZE = (SIZE_X,SIZE_Y)

# Movements speeds differ depending on the player's team
STEP_X = [10, 3, 5]
STEP_Y = [10, 3, 5]

# Server
IP = extractingIP()

# Player
SIZE_MAX_PSEUDO = 10

PLAYER_SIZE = Size(20, 20)

# Maybe not mandatory
WAITING_TIME = 0.0001 # in seconds - period of connection requests when trying to connect to the host

HOST = str(IP)
PORT = 9998

MAINSOCKET = None
LOCK = None
BACKLOG = 1
dicoSocket = {}
#waitingConnectionList = []
waitingDisconnectionList = []


LISTENING = True
MANAGING = True
STOP = False

### Game
# Lobby
LOBBY = True

TEAMSID = {0 : "Not assigned", 1 : "Seekers", 2 : "Hidders"}
READY = {}

# In-game
DEAD = {}

# ----------------------- Variables -----------------------
dicoJoueur = {} # Store players' Player structure

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
    inputWord = extractWord(s)
    Rules(inputWord,pseudo)
    return(states(pseudo))

def processDisconection(ip, s):
    pseudo = extractPseudo(s)
    if not(validIp(ip, pseudo)):
        return("You are impersonating someone else !")
    id, _, _, _, _ = dicoJoueur[pseudo].toList()
    dicoJoueur.pop(pseudo)
    READY.pop(pseudo)
    DEAD.pop(pseudo)
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

def extractWord(s):
    parts = s.split(" ")
    return(parts[2])


def dummyLights():
    l0 = Light(Position(int(200),int(200)))
    l1 = Light(Position(int(500),int(800)))
    l2 = Light(Position(int(1500),int(500)))
    #l01 = Light(Position(int(100),int(800)))
    return([l0,l1,l2])

def states(pseudo):
    player = 0
    liste = []
    out = ""
    
    listOfPlayers = []
    listOfAlivePlayers = []
    listOfWalls = []
    
    
    for key in dicoJoueur:
        p = dicoJoueur[key]
        if key == pseudo:
            player = p
        listOfPlayers.append(p)
        if not DEAD[pseudo]:
            listOfAlivePlayers.append(p)
        
    for key in dicoMur:
        listOfWalls.append(dicoMur[key])
    
    
    if not LOBBY and not DEAD[pseudo]:
        listOfLights = dummyLights()
        
        shadows = Visible(player,listOfLights,listOfAlivePlayers+listOfWalls,SIZE_X,SIZE_Y)
        visiblePlayer = allVisiblePlayer(shadows,listOfAlivePlayers)
        formatshadows = sendingFormat(shadows)
        
        liste.append(str(player))
        for key in visiblePlayer:
            p = dicoJoueur[key]
            if key != pseudo:
                liste.append(str(p))

        out = "STATE "+(str(liste)).replace(" ","")+" SHADES "+formatshadows+" END"

        return(out)
    else:
        for p in listOfPlayers:
            liste.append(str(p))
        
        if LOBBY:
            rlist = []
            for key in READY:
                if READY[key]:
                    rlist.append(key) # List of ready players' username
            
            out += "LOBBY " + str(rlist).replace(" ", "") + " "
        
        out += "STATE "+(str(liste)).replace(" ","")+" END"
        
        return out

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
    id, _, _, position1, size1 = dicoJoueur[pseudo].toList()
    x,y=position1.x,position1.y

    tempId = id

    match inputLetter:
        case ".":
            pass
        case "RIGHT":
            x+=STEP_X[id]
        case "LEFT":
            x-=STEP_X[id]
        case "UP":
            y-=STEP_Y[id]
        case "DOWN":
            y+=STEP_Y[id]
        case "RED":
            if LOBBY:
                tempId = 1
        case "BLUE":
            if LOBBY:
                tempId = 2
        case "NEUTRAL":
            if LOBBY:
                tempId = 0
        case "READY":
            if LOBBY:
                READY[pseudo] = not READY[pseudo]
        case _ :
            return("Invalid Input")
    if tempId != id:
        dicoJoueur[pseudo].update(teamId=tempId)
    if correctPosition(pseudo, x,y,size1.w,size1.h):
        dicoJoueur[pseudo].update(position=Position(x, y), size=Size(size1.w, size1.h))
    launchGame(checkReady())
    return()

def checkReady():
    for pseudo in READY:
        if not READY[pseudo]:
            return False
    
    return True

def launchGame(ready):
    global LOBBY
    
    if ready:
        LOBBY = False

def correctPosition(pseudo, x,y,dx,dy):
    # The player is dead and can not move
    if DEAD.get(pseudo,False):
        return False
    
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
            _, username, _, position, size = dicoJoueur[key].toList()
            
            if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
                
                # players should be able to catch others only if the game started (LOBBY = False)
                if (not LOBBY and id != dicoJoueur[pseudo].teamId):
                    pid = dicoJoueur[pseudo].teamId
                    
                    if id == 2 and pid == 1:
                        DEAD[username] = True
                        return False # The player caught a hidder and can thus move on its previous position
                    elif pid == 2 and id == 1:
                        DEAD[pseudo] = True
                        return True # The player got caught and can no longer move
                
                return True
    
    return False



# ----------------------- Init of a new Player -----------------------


def initNewPlayer(ip, pseudo):
    size = sizeNewPlayer()
    dx,dy=size.w,size.h
    
    pos = positionNewPlayer(dx, dy)
    x,y=pos.x,pos.y
    
    while not correctPosition(pseudo, x, y, dx, dy):
        pos = positionNewPlayer(dx, dy)
        x,y=pos.x,pos.y
    
    color = colorNewPlayer()
    dicoJoueur[pseudo] = Player(ip, 0, pseudo, color, pos, size)
    READY[pseudo] = False
    DEAD[pseudo] = False

def sizeNewPlayer():
    return PLAYER_SIZE

def positionNewPlayer(dx, dy):
    return Position(randint(0, int(SIZE_X - dx)), randint(0, int(SIZE_Y - dy)))

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
                MAINSOCKET.shutdown(SHUT_RDWR)
                MAINSOCKET.close()
                
                print("Socket server closed !")
                
                for (username,(sock,addr)) in dicoSocket:
                    sock.shutdown(SHUT_RDWR)
                    sock.close()
                
                print("Client sockets closed !")
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
    
    #global waitingConnectionList
    
    while not STOP:
        while LISTENING and not STOP:
            try:
                sock, addr = MAINSOCKET.accept()
                in_ip = addr[0]
                
                if(LISTENING):
                    data = sock.recv(1024).strip()
                    
                    print("{} wrote:".format(in_ip))
                    in_data = str(data,'utf-16')
                    print(in_data)
                    
                    out = processRequest(in_ip ,in_data)
                    message = out.split(' ')
                    
                    if message[0]=="CONNECTED":
                        LOCK.acquire()
                        username = message[1]
                        dicoSocket[username] = (sock, addr)
                        LOCK.release()
                    #    waitingConnectionList.append((username, sock, addr))

                    print(">>> ",out,"\n")
                    try:
                        sock.sendall(bytes(out,'utf-16'))
                    except:
                        print("New connection from " + str(in_ip) + " failed!")
                else:
                    print("Connection attempt from " + str(in_ip) + " | Refused : LISTENING = " + str(LISTENING))
            except Exception as e:
                traceback.print_exc()
                print("The main socket was closed. LISTENING = " + str(LISTENING) + " STOP = " + str(STOP))
            
            time.sleep(WAITING_TIME)
        
        time.sleep(WAITING_TIME)

def listen_old():
    global STOP
    global MANAGING
    
    #global waitingConnectionList
    global waitingDisconnectionList
    
    while not STOP:
        while MANAGING and not STOP:
            # coSocketList = waitingConnectionList.copy()
            # waitingConnectionList = []
            
            # for elt in coSocketList:
            #     username, sock, addr = elt[0], elt[1], elt[2]
            #     dicoSocket[username] = sock, addr
            

            
            for elt in waitingDisconnectionList:
                username, sock, addr = elt[0], elt[1], elt[2]
                dicoSocket.pop(username)
                
                # deco remaining player with same ip if needed.
                for username in dicoJoueur:
                    if dicoJoueur[username].ip == addr[0]:
                        id, _, _, _, _ = dicoJoueur[username].toList()
                        dicoJoueur.pop(username)
                        READY.pop(username)
                        DEAD.pop(username)
                        break
                
                sock.close()
            waitingDisconnectionList = []


            LOCK.acquire()
            for username in dicoSocket:
                sock = dicoSocket[username][0]
                addr = dicoSocket[username][1]

                data = sock.recv(1024).strip()
                
                in_ip = addr[0]
                
                print("{} wrote:".format(in_ip))
                in_data = str(data,'utf-16')
                print(in_data)
                
                out = processRequest(in_ip ,in_data)
                message = out.split(" ")
                        
                if message[0]=="DISCONNECTED":
                    username = message[1]
                    waitingDisconnectionList.append((username, sock, addr))
                
                print(">>> ",out,"\n")
                try:
                    sock.sendall(bytes(out,'utf-16'))
                except:
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

