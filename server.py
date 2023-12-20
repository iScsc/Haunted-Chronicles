
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
STEP_X = [10, 4, 3]
STEP_Y = [10, 4, 3]

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
TIME_TO_SWITCH = 10 # Time before switching from lobby to the game when everyone is ready, and from game to lobby when the game is finished.

# Lobby
LOBBY = True

TEAMSID = {"Not assigned" : 0, "Seekers" : 1, "Hidders" : 2}
READY = {}

# In-game
FINISHED = False
DEAD = {}

SEEKING_TIME = 20 # Time to seek for the hidders - in seconds
CURRENT_INGAME_TIME = None # Current in-game time left - in seconds
game_start_time = None

TRANSITION_TIME = 5 # Time to wait for transitions from LOBBY to GAME and vice-versa - in seconds
CURRENT_TRANSITION_TIME = None # Current transition time left - in seconds
transition_start_time = None

# ----------------------- Variables -----------------------

dicoJoueur = {} # Store players' Player structure

dicoSocket = {} # Store clients' (sock, addr) structures where sock is the socket used for communicating, and addr = (ip, port)
waitingDisconnectionList = []

dicoMur = {}
WALLS = [] # List of walls

LIGHTS = []
STATIC_SHADOW = None
LIST_STATIC_SHADOW = []

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

    if not LOBBY:
        return("The game has already started")

    pseudo = extractPseudo(s)
    
    if validPseudo(pseudo):
        return("This Pseudo already exists")
    elif len(pseudo)>SIZE_MAX_PSEUDO:
        return("Your pseudo is too big !")
    elif [c for c in pseudo if c in [" ", ",", "(", ")"]] != []:
        return("Don't use ' ' or ',' or '(' or ')' in your pseudo !")
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
    rules(inputWord,pseudo)
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
    return("DISCONNECTED " + pseudo + " END")


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
    parts = s.split(" ")
    
    if parts[0] == "CONNECT":
        i = 1
        
        while parts[i] != "END" and i < len(parts) - 1:
            pseudo += parts[i] + " "
            i+=1
        
        pseudo = pseudo[:-1]
    else:
        pseudo = parts[1]
    
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
    
    
    # In-game messages
    if not LOBBY:
        # In a transition state from Game to Lobby
        if not None in [TRANSITION_TIME, transition_start_time]:
            out += "TRANSITION_GAME_LOBBY " + checkForWin().replace(" ", "_") + "_Going_back_to_lobby_in_{time:.1f}s ".format(time=CURRENT_TRANSITION_TIME)
        else:
            out += "GAME " + "{time:.1f} ".format(time=CURRENT_INGAME_TIME)
        
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

            out += "STATE "+(str(liste)).replace(" ","")+" SHADES "+formatShadows+" END"
            
        else:            
            for p in listOfAlivePlayers:
                liste.append(str(p))
                    
            out += "STATE "+(str(liste)).replace(" ","")+" SHADES [] END"

        return out
    # Lobby messages
    else:
        # In a transition state from Lobby to Game
        if not None in [TRANSITION_TIME, transition_start_time]:
            out += "TRANSITION_LOBBY_GAME Entering_game_in_{time:.1f}s ".format(time=CURRENT_TRANSITION_TIME)
        else:
            rlist = []
            for key in READY:
                if READY[key]:
                    rlist.append(key) # List of ready players' username
            
            n = len(rlist)
            strList = "["
            for i in range(n):
                if i != n - 1:
                    strList += rlist[i] + ","
                else:
                    strList += rlist[i]
            strList += "]"
            
            out += "LOBBY " + strList + " "
        
        for p in listOfPlayers:
            liste.append(str(p))
        
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

def rules(inputLetter:str,pseudo:str):
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
            if LOBBY and not READY[pseudo]:
                tempId = TEAMSID["Seekers"]
        case "BLUE":
            if LOBBY and not READY[pseudo]:
                tempId = TEAMSID["Hidders"]
        case "NEUTRAL":
            if LOBBY and not READY[pseudo]:
                tempId = TEAMSID["Not assigned"]
        case "READY":
            if LOBBY and id != 0:
                READY[pseudo] = not READY[pseudo]
        case _ :
            return("Invalid Input")
    if tempId != id:
        dicoJoueur[pseudo].update(teamId=tempId)
    if correctPosition(pseudo, x,y,size1.w,size1.h):
        dicoJoueur[pseudo].update(position=Position(x, y), size=Size(size1.w, size1.h))
    
    # rules can launch transition only from LOBBY to GAME
    if LOBBY:
        waitForTransition(cancel=(not (checkReady() and noEmptyTeams())))
    return


def checkForWin():
    """Did a team win the game?"""
    if LOBBY:
        return ""
    else:
        if CURRENT_INGAME_TIME <= 0:
            return "The hidders won the game!"
        else:
            every1dead = True # by default, but updated right afterwards
            
            for pseudo in dicoJoueur:
                if dicoJoueur[pseudo].teamId == TEAMSID["Hidders"]:
                    every1dead = every1dead and DEAD.get(pseudo,False)
            
            if every1dead:
                return "The seekers won the game!"
        
        return "None of both teams have won the game yet."


def checkReady():
    """Are all players ready?"""
    for pseudo in READY:
        if not READY[pseudo]:
            return False
    
    return True

def noEmptyTeams():
    """Are both Seekers and Hidders teams not empty?"""
    teamCounts = {TEAMSID[i] : 0 for i in TEAMSID}
    n = len(teamCounts)
    
    # problem with the server variables, TEAMSID should always have at least 3 different teams
    if n <= 2:
        return False
    
    for pseudo in dicoJoueur:
        teamId, _, _, _, _ = dicoJoueur[pseudo].toList()
        
        if teamId in teamCounts:
            teamCounts[teamId] += 1
    
    return teamCounts[TEAMSID["Hidders"]] > 0 and teamCounts[TEAMSID["Seekers"]] > 0


def switchGameState(ready:bool=None):
    """Switch from lobby to game or vice-versa. If no parameters are used, it will switch to the other state automatically"""
    global LOBBY
    
    if ready == None:
        ready = LOBBY

    if LOBBY == ready:
        LOBBY=not ready
        
        # in game
        if not LOBBY:
            launchGame()
        # in lobby
        else:
            resetGameState()
    # stop transition state
    waitForTransition(cancel=True)


def waitForTransition(cancel=False):
    """Start a transition timer before switching lobby <-> game (not done in the function itself) or cancel a current timer if cancel = True"""
    global CURRENT_TRANSITION_TIME
    global transition_start_time
    
    if cancel:
        CURRENT_TRANSITION_TIME = None
        transition_start_time = None
    
    elif not cancel and None in [CURRENT_TRANSITION_TIME, transition_start_time]:
        CURRENT_TRANSITION_TIME = TRANSITION_TIME
        transition_start_time = time.time()


def launchGame():
    """Set the basic state of the game when launching a new game"""
    global CURRENT_INGAME_TIME
    global game_start_time
    global FINISHED
    
    FINISHED = False

    CURRENT_INGAME_TIME = SEEKING_TIME
    game_start_time = time.time()


def resetGameState():
    """Reset the current state of the game to get ready for a new game"""
    global CURRENT_INGAME_TIME
    global game_start_time
    
    global READY
    global DEAD
    
    CURRENT_INGAME_TIME = None
    game_start_time = None
    for pseudo in dicoJoueur:
        _, _, _, _, size = dicoJoueur[pseudo].toList()
        READY[pseudo] = False
        DEAD[pseudo] = False
        
        dicoJoueur[pseudo].update(position=randomValidPosition(pseudo, size.w, size.h))


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
        if key != pseudo and not DEAD.get(key, False):
            pid, username, _, position, size = dicoJoueur[key].toList()
            
            if abs(c[0] - position.x - size.w/2) < (dx + size.w)/2 and abs(c[1] - position.y - size.h/2) < (dy + size.h)/2:
                
                # players should be able to catch others only if the game started (LOBBY = False)
                if (not LOBBY and not FINISHED and id != pid):
                    
                    if id == TEAMSID["Seekers"] and pid == TEAMSID["Hidders"]:
                        DEAD[username] = True
                        return False # The player caught a hidder and can thus move on its previous position
                    elif pid == TEAMSID["Hidders"] and id == TEAMSID["Seekers"]:
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
    
    pos = positionNewPlayer(pseudo, dx, dy)
    
    color = colorNewPlayer()
    dicoJoueur[pseudo] = Player(0, pseudo, color, pos, size)
    READY[pseudo] = False
    DEAD[pseudo] = False

    
def sizeNewPlayer():
    """A size for a new player (fixed)"""
    return PLAYER_SIZE

  
def positionNewPlayer(pseudo, dx, dy):
    """A position for a new player (random)"""
    return randomValidPosition(pseudo, dx, dy)


def colorNewPlayer():
    """A color for a new player (random)"""
    return Color(randint(1,255),randint(1,255),randint(1,255))


def randomValidPosition(pseudo, dx, dy):
    """Generate a random valid position"""
    
    pos = Position(randint(0, int(SIZE_X - dx)), randint(0, int(SIZE_Y - dy)))
    x,y=pos.x,pos.y
    
    while not correctPosition(pseudo, x, y, dx, dy):
        pos = Position(randint(0, int(SIZE_X - dx)), randint(0, int(SIZE_Y - dy)))
        x,y=pos.x,pos.y
    
    return pos

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
                print("LOBBY = ", LOBBY)
                
                
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
                        
                        in_data = str(data,'utf-8')
                        
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
                            sock.sendall(bytes(out,'utf-8'))
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
    
    global CURRENT_INGAME_TIME
    global CURRENT_TRANSITION_TIME
    
    global FINISHED
    
    while not STOP:
        while MANAGING and not STOP:
            
            for elt in waitingDisconnectionList:
                username, sock, addr = elt[0], elt[1], elt[2]
                
                if username in dicoSocket and dicoSocket[username] == (sock, addr):
                    dicoSocket.pop(username)
                    dicoJoueur.pop(username)
                    READY.pop(username)
                    DEAD.pop(username)
                
                sock.close()
            waitingDisconnectionList = []

            LOCK.acquire()
            for username in dicoSocket:
                sock, addr = dicoSocket[username]

                try:
                    data = sock.recv(1024).strip()
                    
                    in_ip = addr[0]

                    in_data = str(data,'utf-8')
                    
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
                        sock.sendall(bytes(out,'utf-8'))
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
            
            # Not in a transition state
            if None in [CURRENT_TRANSITION_TIME, transition_start_time]:
                
                # In game
                if not (None in [CURRENT_INGAME_TIME, game_start_time]):
                    CURRENT_INGAME_TIME = SEEKING_TIME - (time.time() - game_start_time)
                    if CURRENT_INGAME_TIME < 0:
                        CURRENT_INGAME_TIME = 0
                
                # game finished
                if not LOBBY and (len(dicoSocket.keys())==0 or not "None" in checkForWin()):
                    FINISHED = True
                    waitForTransition()
            
            # In a transition state
            else:
                CURRENT_TRANSITION_TIME = TRANSITION_TIME - (time.time() - transition_start_time)
                
                if CURRENT_TRANSITION_TIME <= 0:
                    switchGameState()
            
            time.sleep(WAITING_TIME)
        
        time.sleep(WAITING_TIME)
    


# Some static lights
def dummyLights():
    """Some static lights"""
    l0 = Light(Position(int(200),int(200)))
    l1 = Light(Position(int(500),int(800)))
    l2 = Light(Position(int(1500),int(500)))
    #l01 = Light(Position(int(100),int(800)))
    L = [dicoMur[l] for l in dicoMur if dicoMur[l].color == Light.BASE_COLOR]
    return(L)#[l0,l1,l2])

def baseInit():
    global dicoMur
    global WALLS
    global LIGHTS
    global STATIC_SHADOW
    global LIST_STATIC_SHADOW
    
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

    dicoMur[19] = Wall(17, Light.BASE_COLOR, Position(200,200), Light.BASE_SIZE)
    dicoMur[20] = Wall(18, Light.BASE_COLOR, Position(500,800), Light.BASE_SIZE)
    dicoMur[21] = Wall(17, Light.BASE_COLOR, Position(1500, 500), Light.BASE_SIZE)


    # list of walls
    for key in dicoMur:
        if dicoMur[key].color != Light.BASE_COLOR:
            WALLS.append(dicoMur[key])
    
    t1 = time.time()
    LIGHTS = dummyLights()
    STATIC_SHADOW = AllSources(LIGHTS, WALLS, SIZE_X, SIZE_Y)
    LIST_STATIC_SHADOW = [OneSource(l, WALLS, SIZE_X, SIZE_Y) for l in LIGHTS]
    t2 = time.time()
    print("time of precalculation : ",t2-t1," s")

# ----------------------- Main -----------------------
def main():
    """Main function launching the parallel threads to manage the different aspects of the server.
    """
    global MAINSOCKET
    global LOCK
    
    # Initialization
    baseInit()
    if MAINSOCKET == None:
        MAINSOCKET = socket(AF_INET, SOCK_DGRAM)
        MAINSOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        MAINSOCKET.bind((HOST, PORT))
    
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

