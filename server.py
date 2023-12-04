
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
    """The host IP"""
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

# Sockets main variable
MAINSOCKET = None
LOCK = None
BACKLOG = 1

# Server managing variables
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

# list of walls
WALLS = []
for key in dicoMur:
    WALLS.append(dicoMur[key])

# Some static lights
def dummyLights():
    """Some static lights"""
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
def processRequest(ip, s:str):
    """Calls the right function according to process a request

    Args:
        ip : player IP
        s (str): the request to process
        
    Returns:
        A string representing the connection of the player and/or the state of the server or why the request was invalid
    """
    type = typeOfRequest(s)
    if type == "CONNECT":
        return(processConnect(s))
    elif type == "INPUT":
        return(processInput(ip, s))
    elif type == "DISCONNECTION":
        return(processDisconnection(ip, s))
    else :
        return("Invalid Request")


def processConnect(s:str):
    """Process a connection request

    Args:
        s (str): the connection request ("CONNECT <username> END")
        
    Returns:
        A string representing the connection of the player and the state of the server or why the connection request was invalid
    """
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
    
    
def processInput(ip, s:str):
    """Process an 'input' request

    Args:
        ip : player IP
        s (str): the input request ("INPUT <username> <input> END")
        
    Returns:
        A string representing the state of the server or why the connection request was invalid
    """
    pseudo = extractPseudo(s)
    if not(validPseudo(pseudo)):
        return("No player of that name")
    if not(validIp(ip, pseudo)):
        return("You are impersonating someone else !")
    inputWord = extractWord(s)
    Rules(inputWord,pseudo)
    return(states(pseudo))


def processDisconnection(ip, s:str):
    """Process a disconnection request

    Args:
        s (str): the disconnection request ("DISCONNECT <username> END")
        
    Returns:
        "DISCONNECTED <username> END" or why the connection request was invalid
    """
    pseudo = extractPseudo(s)
    if not(validIp(ip, pseudo)):
        return("You are impersonating someone else !")
    id, _, _, _, _ = dicoJoueur[pseudo].toList()
    dicoJoueur.pop(pseudo)
    READY.pop(pseudo)
    DEAD.pop(pseudo)
    return("DISCONNECTED" + s[13:])


def typeOfRequest(s:str):
    """The type of a request (CONNECT,INPUT,DISCONNECT)"""
    type = ""
    i = 0
    n = len(s)
    while i<n and s[i]!=" ":
        type+=s[i]
        i+=1
    return(type)


def extractPseudo(s:str):
    """The pseudo of a player from a connection request"""
    pseudo = ""
    n = len(s)
    i0 = len(typeOfRequest(s)) + 1
    i = i0
    while i<n and s[i]!=" ":
        pseudo+=s[i]
        i+=1
    return(pseudo)

  
def extractWord(s):
    """The input word from the 's' input request string"""
    parts = s.split(" ")
    return(parts[2])
  

def states(pseudo:str):
    """The state of the server modulo what the player can see

    Args:
        pseudo (str): player pseudo
        
    Returns:
        A string representing the state of the server
    """
    player = 0 # the player
    liste = [] # list of player strings
    listOfPlayers = [] # list of all players
    listOfAlivePlayers = [] # list of players that have not been caught yet
    
    out="" # string to send back
    
    # gets all player
    for key in dicoJoueur:
        p = dicoJoueur[key]
        if key == pseudo:
            player = p
        listOfPlayers.append(p)
        if not DEAD[key]:
            listOfAlivePlayers.append(p)
    
    
    if not LOBBY:
        if not DEAD[pseudo]:
            
            shadows = Visible(player, LIGHTS, listOfAlivePlayers, SIZE_X, SIZE_Y, STATIC_SHADOW, WALLS, LIST_STATIC_SHADOW)
            visiblePlayer = allVisiblePlayer(shadows,listOfAlivePlayers)
            formatShadows = sendingFormat(shadows)

            # gets visible player strings
            liste.append(str(player))
            for key in visiblePlayer:
                p = dicoJoueur[key]
                if key != pseudo:
                    liste.append(str(p))

            out = "STATE "+(str(liste)).replace(" ","")+" SHADES "+formatShadows+" END"

            return(out)
        else:            
            for p in listOfAlivePlayers:
                liste.append(str(p))
                    
            out = "STATE "+(str(liste)).replace(" ","")+" SHADES [] END"


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
    """Formated wall string "WALLS <wallstring> END" """
    liste = []
    for key in dicoMur:
        liste.append(str(dicoMur[key]))
    out = "WALLS " + (str(liste)).replace(" ","") + " END"
    return(out)


def firstConnection(pseudo:str):
    """Formated string for first connections:
        "CONNECTED <username> <size> WALLS <wallstring> STATE <statestring> SHADES <shadestring> END" """
    out = "CONNECTED " + pseudo + " " + (str(SIZE)).replace(" ","") + " " + walls().replace("END","") + states(pseudo)
    return(out)


def validPseudo(pseudo:str):
    """If the pseudo exists"""
    return(pseudo in dicoJoueur.keys())


def validIp(ip, pseudo:str):
    """If the pseudo and a socket with the ip exist and they are associated"""
    return (pseudo in dicoJoueur.keys() and pseudo in dicoSocket.keys() and dicoSocket[pseudo][1][0] == str(ip))



# ----------------------- Games Rules -----------------------

def Rules(inputLetter:str,pseudo:str):
    """Process an input for a player

    Args:
        inputLetter (char): input letter
        pseudo (str): player pseudo
    Returns:
        "Invalid Input" if the input did not respect the rules, else None
    """
    
    global READY
    
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
    return


def checkReady():
    """Are all players ready?"""
    for pseudo in READY:
        if not READY[pseudo]:
            return False
    
    return True

  
def launchGame(ready):
    """Exit lobby"""
    global LOBBY
    
    if ready:
        LOBBY = False

        
def correctPosition(pseudo:str, x:int,y:int,dx:int,dy:int):
    """If a position is inside the level boundaries and does not overlap walls or other players

    Args:
        pseudo (str): player pseudo
        x (int): player x position
        y (int): player y position
        dx (int): player width
        dy (int): player height

    Returns:
        bool: is the position valid for player 'pseudo'?
    """
    # The player is dead and can not move
    if DEAD.get(pseudo,False):
        return False
    correctX = (x>=0) and (x+dx <= SIZE_X)
    correctY = (y>=0) and (y+dy <= SIZE_Y)
    
    return correctX and correctY and not collision(pseudo, x, y, dx, dy)


def collision(pseudo:str, x:int, y:int, dx:int, dy:int):
    """If a position does not overlap walls or other players

    Args:
        pseudo (str): player pseudo
        x (int): player x position
        y (int): player y position
        dx (int): player width
        dy (int): player height

    Returns:
        bool: is the position not making player 'pseudo' overlap walls or other?
    """
    global DEAD
    
    id = 0
    if pseudo in dicoJoueur:
        id, _, _, _, _ = dicoJoueur[pseudo].toList()
        
    c = (x + dx/2, y + dy/2)
    
    for key in dicoMur.keys():
        _, _, position, size = dicoMur[key].toList()
        
        if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
            return True
    
    for key in dicoJoueur.keys():
        if key != pseudo:
            pid, username, _, position, size = dicoJoueur[key].toList()
            
            if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
                
                # players should be able to catch others only if the game started (LOBBY = False)
                if (not LOBBY and id != pid):
                    
                    if id == 2 and pid == 1:
                        DEAD[username] = True
                        return False # The player caught a hidder and can thus move on its previous position
                    elif pid == 2 and id == 1:
                        DEAD[pseudo] = True
                        return True # The player got caught and can no longer move
                
                return True
    
    return False



# ----------------------- Init of a new Player -----------------------

def initNewPlayer(pseudo:str):
    """Creates a new player 'pseudo'

    Args:
        pseudo (str): the player pseudo
    """
    size = sizeNewPlayer()
    dx,dy=size.w,size.h
    
    pos = positionNewPlayer(dx, dy)
    x,y=pos.x,pos.y
    
    while not correctPosition(pseudo, x, y, dx, dy):
        pos = positionNewPlayer(dx, dy)
        x,y=pos.x,pos.y
    
    color = colorNewPlayer()
    dicoJoueur[pseudo] = Player(0, pseudo, color, pos, size)
    READY[pseudo] = False
    DEAD[pseudo] = False

    
def sizeNewPlayer():
    """A size for a new player (fixed)"""
    return PLAYER_SIZE

  
def positionNewPlayer(dx, dy):
    """A position for a new player (random)"""
    return Position(randint(0, int(SIZE_X - dx)), randint(0, int(SIZE_Y - dy)))


def colorNewPlayer():
    """A color for a new player (random)"""
    return Color(randint(1,255),randint(1,255),randint(1,255))



# ----------------------- Threads -----------------------

def manage_server():
    """Manage console inputs"""
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
                except (OSError):
                    if DEBUG:
                        traceback.print_exc()
                    print("MAINSOCKET could not be shutdown")
                MAINSOCKET.close()
                
                print("Socket server closed !")
                
                for username, (sock,addr) in dicoSocket.items():
                    try:
                        sock.shutdown(SHUT_RDWR)
                    except (OSError):
                        if DEBUG:
                            traceback.print_exc()
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
    """Manage first connections and connection request"""
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
                        except (OSError):
                            if DEBUG:
                                traceback.print_exc()
                            print("New connection from " + str(in_ip) + " failed!")
                    except (OSError):
                        if DEBUG:
                            traceback.print_exc()
                        print("New connection from " + str(in_ip) + " failed!")
                
                else:
                    print("Connection attempt from " + str(in_ip) + " | Refused : LISTENING = " + str(LISTENING))

            except (OSError):
                if DEBUG:
                    traceback.print_exc()
                print("The main socket was closed. LISTENING = " + str(LISTENING) + " and STOP = " + str(STOP))
            
            time.sleep(WAITING_TIME)
        
        time.sleep(WAITING_TIME)

def listen_old():
    """Manage already connected sockets and inputs or disconnection request"""
    global STOP
    global MANAGING
    
    global waitingDisconnectionList
    
    while not STOP:
        while MANAGING and not STOP:
            
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
                    except (OSError):
                        if DEBUG:
                            traceback.print_exc()
                        print("Loss connection while sending data with player " + username + " (ip = " + str(addr[0]) + ")")
                        waitingDisconnectionList.append((username, sock, addr))
                except (OSError):
                    if DEBUG:
                        traceback.print_exc()
                    print("Loss connection while receiving data with player " + username + " (ip = " + str(addr[0]) + ")")
                    waitingDisconnectionList.append((username, sock, addr))
            LOCK.release()
            
            time.sleep(WAITING_TIME)
        
        time.sleep(WAITING_TIME)
    


# ----------------------- Main -----------------------
def main():
    """Main function launching the parallel threads to manage the different aspects of the server.
    """
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

