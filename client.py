# ----------------------- Imports -----------------------
import sys
import pygame as pg
from threading import *

from socket import *

import time

from platform import system

from player import Player
from wall import Wall
from common import *
from interpretor import *
from inlight import toVisible

# ----------------------- Variables -----------------------

DEBUG=True

SERVER_IP = "192.168.1.34" #"localhost"
SERVER_PORT = 9998
CONNECTED = False
DISCONNECTION_WAITING_TIME = 5 # in seconds, time waited before disconnection without confirmation from the host
MAX_REQUESTS = 10 # number of requests without proper response before force disconnect

FPS = 60

SIZE = None
SCALE_FACTOR = None
SCREEN = None

WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)

FONT = "Arial" # Font used to display texts
FONT_SIZE_USERNAME = 25
FONT_SIZE_PING = 12

USERNAME = "John"
PLAYERS = []
WALLS = []
UNVISIBLE = []

SOCKET = None
WAITING_TIME = 0.01 # in seconds - period of connection requests when trying to connect to the host
SOCKET_TIMEOUT = 30 # in seconds
EXIT_TIMEOUT = 5 # in seconds - when trying to disconnect

PING = None # in milliseconds - ping with the server, None when disconnected

LOBBY = True
readyPlayers = []
DEFAULT_LOBBY_COLOR = WHITE
READY_LOBBY_COLOR = GREEN
TEAM_DISPLAY_HEIGHT = 100
RED_TEAM = 1
BLUE_TEAM = 2

WALL_VISIBLE = True


# ----------------------- Threads -----------------------

def display():
    """Thread to display the current state of the game given by the server.
    """
    
    global SCREEN
    global PLAYERS
    global SCALE_FACTOR
    global SIZE
    
    pg.init()
    
    PLATEFORM = system() # system name (Windows or Linux ... )

    if PLATEFORM=="Linux":
        info = pg.display.Info()
        SCALE_FACTOR = info.current_w/SIZE[0],info.current_h/SIZE[1]
        SCREEN = pg.display.set_mode((0,0),pg.FULLSCREEN)
    elif PLATEFORM=="Windows":
        info = pg.display.Info()
        SCALE_FACTOR = info.current_w/SIZE[0],info.current_h/SIZE[1]
        SIZE = info.current_w, info.current_h
        SCREEN = pg.display.set_mode(SIZE)
    else :
        SCALE_FACTOR=1,1
    pingFont = pg.font.SysFont(FONT, FONT_SIZE_PING)
    usernameFont = pg.font.SysFont(FONT, FONT_SIZE_USERNAME)
    
    clock = pg.time.Clock()
    
    while CONNECTED:
        
        SCREEN.fill(BLACK.color)  # May need to be custom
        
        pg.event.pump() # Useless, just to make windows understand that the game has not crashed...
    
        if not LOBBY and WALL_VISIBLE and len(UNVISIBLE) > 2:
            pg.draw.polygon(SCREEN, BLACK.color, [(x*SCALE_FACTOR[0],y*SCALE_FACTOR[1]) for (x,y) in UNVISIBLE])
    
    
        # Walls
        for wall in WALLS:
            pg.draw.rect(SCREEN, wall.color.color, [wall.position.x*SCALE_FACTOR[0], wall.position.y*SCALE_FACTOR[1], wall.size.w*SCALE_FACTOR[0], wall.size.h*SCALE_FACTOR[1]])
        
        
        
        #Unvisible
        if not LOBBY and not(WALL_VISIBLE) and len(UNVISIBLE) > 2:
            pg.draw.polygon(SCREEN, BLACK.color, [(x*SCALE_FACTOR[0],y*SCALE_FACTOR[1]) for (x,y) in UNVISIBLE])
        
        
        # Players
        h=TEAM_DISPLAY_HEIGHT
        for player in PLAYERS:
            pg.draw.rect(SCREEN, player.color.color, [player.position.x*SCALE_FACTOR[0], player.position.y*SCALE_FACTOR[1], player.size.w*SCALE_FACTOR[0], player.size.h*SCALE_FACTOR[1]])
            
            usernameText = player.username
            usernameSize = pg.font.Font.size(usernameFont, usernameText)
            usernameSurface = pg.font.Font.render(usernameFont, usernameText, False, player.color.color)
            
            SCREEN.blit(usernameSurface, (player.position.x*SCALE_FACTOR[0] + (player.size.w*SCALE_FACTOR[0] - usernameSize[0]) // 2, player.position.y*SCALE_FACTOR[1] - usernameSize[1]))            
            if(LOBBY):
                usernamePosition = (SIZE[0]-usernameSize[0])//2
                
                font_color = DEFAULT_LOBBY_COLOR
                
                if(player.teamId == RED_TEAM):
                    usernamePosition = 0
                if(player.teamId == BLUE_TEAM):
                    usernamePosition = SIZE[0]-usernameSize[0]
                
                if(player.username in readyPlayers):
                    font_color = READY_LOBBY_COLOR

                usernameSurface = pg.font.Font.render(usernameFont, usernameText, False, font_color.color)
                SCREEN.blit(usernameSurface, (usernamePosition, h))
                h+=usernameSize[1]
                
        
            
        
        #lights
        if DEBUG:
            pg.draw.rect(SCREEN, (255,255,0), [200, 200, 10, 10])
            pg.draw.rect(SCREEN, (255,255,0), [500, 800, 10, 10])
            pg.draw.rect(SCREEN, (255,255,0), [1500, 500, 10, 10])
 
        # Ping
        pingText = "Ping : " + str(PING) + " ms"
        pingSize = pg.font.Font.size(pingFont, pingText)
        
        pingSurface = pg.font.Font.render(pingFont, pingText, False, WHITE.color)
        
        SCREEN.blit(pingSurface, (SIZE[0] - pingSize[0], 0))
        
        
        # End
        pg.display.update()
        
        clock.tick(FPS)



def game():
    """Thread to send inputs to the server, receive the current state of the game from it, and update the client-side variables.
    """
    
    global PLAYERS
    global SERVER_IP
    global SERVER_PORT
    global SOCKET
    global LOBBY
    
    
    requestNumber=0
    
    clock = pg.time.Clock()
    
    while CONNECTED and requestNumber<MAX_REQUESTS:
        
        inputs = getInputs()
        
        state = send(inputs)
        

        
        if (update(state)) :
            requestNumber+=1
        else :
            requestNumber=0
        
        if requestNumber>=MAX_REQUESTS:
            
            if DEBUG:
                print("Max number of request has been passed for inputs!")
                
            exitError()

        
        clock.tick(FPS)
    
    if SOCKET != None:
        SOCKET.close()
        SOCKET = None



# ----------------------- Functions -----------------------

def connect():
    """Try to connect to the given SERVER_IP and SERVER_PORT. When successful, initialize the current state of the game.

    Returns:
        bool: is the connection successful ?
    """
    
    global SIZE
    
    message = send("CONNECT " + USERNAME + " END") # Should be "CONNECTED <Username> SIZE WALLS <WallsString> STATE <PlayersString> END"
    
    messages = message.split(" ")
    
    if DEBUG:
        print(message)
    
    if (len(messages) == 10 and messages[0] == "CONNECTED" and messages[1] == USERNAME and messages[3] == "WALLS" and messages[5] == "LOBBY" and messages[7] == "STATE" and messages[9] == "END"):
        
        try:
            sizeStr = "" + messages[2]
            sizeStr = sizeStr.replace("(", "")
            sizeStr = sizeStr.replace(")", "")
            
            sizeStr = sizeStr.split(",")
            
            SIZE = (int(sizeStr[0]), int(sizeStr[1]))
        except:
            if DEBUG:
                print("Size Error ! Size format was not correct !")
            SIZE = (400, 300)   # Some default size.
        
        beginWallIndex = len(messages[0]) + len(messages[1]) + len(messages[2]) + 3 # 3 characters 'space'
        beginPlayerIndex = len(messages[0]) + len(messages[1]) + len(messages[2]) + len(messages[3]) + len(messages[4]) + 5 # 5 characters 'space'
        
        update(message[beginWallIndex : beginPlayerIndex - 1] + " END") # Walls
        update(message[beginPlayerIndex:]) #Players and Shades
        
        return True
    # Manage failed connections
    elif "CONNECTED" not in messages:
        askNewPseudo(message)
        
        global SOCKET
        
        SOCKET.close()
        SOCKET = None

    return False



def askNewPseudo(errorMessage):
    """Ask for another username when connection fails to try to connect again.

    Args:
        errorMessage (str): connection error message sent back by the server when the connection failed.
    """
    global USERNAME
    
    print("Server sent back : " + errorMessage)
    print("Please try a new pseudo. (Your previous one was " + USERNAME + ")")
    
    username = ""
    
    while username == "":
        username = input()
    
    USERNAME = username



def getInputs():
    """Get inputs from the keyboard and generate the corresponding request to send to the server.

    Returns:
        str: the normalized request to send to the server : "INPUT <Username> <Input> END"
    """
    
    events = pg.event.get()
    
    keys = pg.key.get_pressed()
    
    for event in events:
        if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
            exit()
    
    if keys[pg.K_LEFT] or keys[pg.K_q]:
        return "INPUT " + USERNAME + " LEFT END"
    elif keys[pg.K_RIGHT] or keys[pg.K_d]:
        return "INPUT " + USERNAME + " RIGHT END"
    elif keys[pg.K_UP] or keys[pg.K_z]:
        return "INPUT " + USERNAME + " UP END"
    elif keys[pg.K_DOWN] or keys[pg.K_s]:
        return "INPUT " + USERNAME + " DOWN END"
    elif keys[pg.K_r]:
        return "INPUT " + USERNAME + " RED END"
    elif keys[pg.K_b]:
        return "INPUT " + USERNAME + " BLUE END"
    elif keys[pg.K_n]:
        return "INPUT " + USERNAME + " NEUTRAL END"
    elif keys[pg.K_SPACE]:
        return "INPUT " + USERNAME + " READY END"
    
    return "INPUT " + USERNAME + " . END"



def send(input="INPUT " + USERNAME + " . END"):
    """Send a normalized request to the server and listen for the normalized answer.

    Args:
        input (str): Normalized request to send to the server. Defaults to "INPUT <Username> . END".

    Returns:
        str: the normalized answer from the server.
    """
    
    global PING
    global SOCKET
    
    # Initialization
    if (SOCKET == None and input[0:7] == "CONNECT"):
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.settimeout(SOCKET_TIMEOUT)
        SOCKET.connect((SERVER_IP, SERVER_PORT))
    
    
    # Usual behavior
    if SOCKET != None:
        t = time.time()

        # send data
        try:
            SOCKET.sendall(bytes(input, "utf-16"))
            
            # receive answer
            answer = str(SOCKET.recv(1024*16), "utf-16")
            
            PING = int((time.time() - t) * 1000)
            
            return answer
        except:
            exitError("Loss connection with the remote server.")



def update(state="STATE [] END"):
    """Update the local variables representing the current state of the game from the given state.

    Args:
        state (str): The normalized state of the game. Defaults to "STATE [] END".
    """
    
    global WALLS
    global PLAYERS
    global UNVISIBLE
    global readyPlayers
    global LOBBY
    
    if state == None or type(state) != str or state == "":
        return False
    
    messages = state.split(" ")
    
    if(messages[0] == "LOBBY"):
        LOBBY = True
    else:
        LOBBY = False
    
    if len(messages) == 3 and messages[0] == "STATE" and messages[2] == "END":
        players = Player.toPlayers(messages[1],DEBUG)
        if (players != None):
            PLAYERS=players
            return False
        else: return True
        
    elif len(messages) == 3 and messages[0] == "WALLS" and messages[2] == "END":
        walls = Wall.toWalls(messages[1],DEBUG)
        if (walls != None):
            WALLS=walls
            return False
        else: return True
        
    elif len(messages) == 3 and messages[0] == "SHADES" and messages[2] == "END":
        unvisible = toVisible(messages[1],DEBUG)
        if (unvisible != None):
            UNVISIBLE=unvisible
            return False
        else: return True
        
    elif len(messages) == 3 and messages[0] == "LOBBY" and messages[2] == "END":
        readyPlayers = interp(messages[1], list=[str, 0])
        return False
        
    elif len(messages) == 5 and messages[0] == "STATE" and messages[2] == "SHADES" and messages[4] == "END":
        return update(messages[0]+" "+messages[1]+" "+messages[4]) or update(messages[2]+" "+messages[3]+" "+messages[4])
    
    elif len(messages) == 5 and messages[0] == "LOBBY" and messages[2] == "STATE" and messages[4] == "END":
        return update(messages[0]+" "+messages[1]+" "+messages[4]) or update(messages[2]+" "+messages[3]+" "+messages[4])
    
    return True

def exit():
    """Send the normalized disconnection request and then exits the game.
    """
    
    global CONNECTED
    global SOCKET
    
    SOCKET.settimeout(EXIT_TIMEOUT)
    
    requestNumber=0
    
    t = time.time()
    while time.time() - t < DISCONNECTION_WAITING_TIME and requestNumber<MAX_REQUESTS:
        requestNumber+=1
        if send("DISCONNECTION " + USERNAME + " END") == "DISCONNECTED " + USERNAME + " END":
            break
    
    if requestNumber>=MAX_REQUESTS:
        
        if DEBUG:
            print("Max number of request has been passed for disconnection!")
                
        exitError()
    
    CONNECTED = False
    SOCKET.close()
    SOCKET = None

def exitError(errorMessage="Sorry a problem occured..."):
    """Exit the game
        Called if there has been a problem with the server"""
        
    global CONNECTED
    global SOCKET
    
    print(errorMessage)
    
    CONNECTED=False
    SOCKET.close()
    SOCKET = None



def main():
    """Main function launching the parallel threads to play the game and communicate with the server.
    """
    
    global CONNECTED
    requestNumber=0
    
    
    while not CONNECTED and requestNumber<MAX_REQUESTS:
        CONNECTED = connect()
        time.sleep(WAITING_TIME)
        requestNumber+=1
    if requestNumber>MAX_REQUESTS:
        
        if DEBUG:
            print("Max number of request has been passed for connections!")
                
        exitError()
    
    
    if CONNECTED:
        displayer = Thread(target=display)
        gameUpdater = Thread(target=game)
        
        displayer.start()
        gameUpdater.start()



# ----------------------- Client Side -----------------------

if __name__ == "__main__":

    if len(sys.argv)==3:
        SERVER_IP = "".join(sys.argv[1]) #"10.193.49.95" #"localhost"
        SERVER_PORT = int("".join(sys.argv[2])) #9998
    
    print("Server IP : ",SERVER_IP)
    print("Server Port : ",SERVER_PORT)

    print("Which username do you want to use ? (By default, it is " + USERNAME + ")")
    username = input()
    
    if username != "":
        USERNAME = username
    
    main()
