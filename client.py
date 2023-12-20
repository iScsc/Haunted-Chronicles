# ----------------------- Imports -----------------------
import sys
import pygame as pg
from threading import *

from socket import *

import time
import traceback

from platform import system

from player import Player
from wall import Wall
from common import *
from interpretor import *
from inlight import toVisible

# ----------------------- Variables -----------------------

DEBUG=False

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

BACKGROUND_COLOR = Color(75, 75, 75)

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

# Teams display
TEAM_DISPLAY_HEIGHT = 100
TEAMS_NAMES = {0 : "Not assigned (press 'N' to join)",
               1 : "Seekers (press 'R' to join)",
               2 : "Hidders (press 'B' to join)"}
TEAMS = {0 : [], 1 : [], 2 : []}
TEAMS_COLOR = {0 : WHITE, 1 : RED, 2 : BLUE}
FONT_SIZE_TEAMS = 30

TEAMS_POSITIONS = {0 : 1, 1 : 0, 2 : 2}
TEAMS_FINAL_POSITIONS = {0 : None, 1 : None, 2 : None}
TEAMS_TEXTS = {0 : None, 1 : None, 2 : None}

WALL_VISIBLE = True

# In-game variables
GAME_TIME = None
# Transitions variables
IN_TRANSITION = False
TRANSITION_TEXT = ""
FONT_SIZE_TRANSITION = 40

# ----------------------- Threads -----------------------

def display():
    """Thread to display the current state of the game given by the server.
    """
    
    global SCREEN
    global PLAYERS
    global SCALE_FACTOR
    global SIZE
    

    global TEAMS
    global TEAMS_FINAL_POSITIONS

    pg.init()
    
    
    PLATEFORM = system() # system name (Windows or Linux ... )

    # sets screen size and scale factors
    if PLATEFORM=="Linux":
        info = pg.display.Info()
        SCALE_FACTOR = info.current_w/SIZE[0],info.current_h/SIZE[1]
        SCREEN = pg.display.set_mode((0,0),pg.FULLSCREEN)
        SIZE=SCREEN.get_size()
    elif PLATEFORM=="Windows":
        info = pg.display.Info()
        SCALE_FACTOR = info.current_w/SIZE[0],info.current_h/SIZE[1]
        SIZE = info.current_w, info.current_h
        SCREEN = pg.display.set_mode(SIZE)
    else :
        SCALE_FACTOR=1,1
    
    
    # set fonts for ping, teams, usernames and in-game printings
    pingFont = pg.font.SysFont(FONT, FONT_SIZE_PING)
    usernameFont = pg.font.SysFont(FONT, FONT_SIZE_USERNAME)
    teamFont = pg.font.SysFont(FONT, FONT_SIZE_TEAMS)
    timeFont = teamFont
    transitionFont = pg.font.SysFont(FONT, FONT_SIZE_TRANSITION)
    
    # set teams display parameters
    baseHeight = TEAM_DISPLAY_HEIGHT
    for id in TEAMS_TEXTS:
        teamSize = pg.font.Font.size(teamFont, TEAMS_NAMES[id])
        
        baseHeight = TEAM_DISPLAY_HEIGHT + teamSize[1]
        
        TEAMS_TEXTS[id] = pg.font.Font.render(teamFont, TEAMS_NAMES[id], False, TEAMS_COLOR[id].color)
        TEAMS_FINAL_POSITIONS[id] = (SIZE[0] - teamSize[0]) // 2 * TEAMS_POSITIONS[id]
    
    
    clock = pg.time.Clock()
    
    
    while CONNECTED:
        
        SCREEN.fill(BACKGROUND_COLOR.color)  # May need to be custom
        
        pg.event.pump() # Useless, just to make windows understand that the game has not crashed...

        if not LOBBY and WALL_VISIBLE and len(UNVISIBLE) > 2: # draws shades under the walls
            pg.draw.polygon(SCREEN, BLACK.color, [(x*SCALE_FACTOR[0],y*SCALE_FACTOR[1]) for (x,y) in UNVISIBLE])

        
        # Walls
        for wall in WALLS:
            pg.draw.rect(SCREEN, wall.color.color, [wall.position.x*SCALE_FACTOR[0], wall.position.y*SCALE_FACTOR[1], wall.size.w*SCALE_FACTOR[0], wall.size.h*SCALE_FACTOR[1]])
        

        #Unvisible
        if not LOBBY and not(WALL_VISIBLE) and len(UNVISIBLE) > 2: #draw shades on top of the walls
            pg.draw.polygon(SCREEN, BLACK.color, [(x*SCALE_FACTOR[0],y*SCALE_FACTOR[1]) for (x,y) in UNVISIBLE])

        
        # Teams display
        if LOBBY:
            for id in TEAMS_NAMES:
                SCREEN.blit(TEAMS_TEXTS[id], (TEAMS_FINAL_POSITIONS[id], TEAM_DISPLAY_HEIGHT))
            
            TEAMS = {0 : [], 1 : [], 2 : []}
        
        
        # Players
        for player in PLAYERS:
            pg.draw.rect(SCREEN, player.color.color, [player.position.x*SCALE_FACTOR[0], player.position.y*SCALE_FACTOR[1], player.size.w*SCALE_FACTOR[0], player.size.h*SCALE_FACTOR[1]])
            
            usernameText = player.username
            usernameSize = pg.font.Font.size(usernameFont, usernameText)
            usernameSurface = pg.font.Font.render(usernameFont, usernameText, False, player.color.color)
            
            SCREEN.blit(usernameSurface, (player.position.x*SCALE_FACTOR[0] + (player.size.w*SCALE_FACTOR[0] - usernameSize[0]) // 2, player.position.y*SCALE_FACTOR[1] - usernameSize[1]))            
            if(LOBBY):
                h = baseHeight
                if player.teamId in TEAMS:
                    TEAMS[player.teamId].append(player)
                    h = baseHeight + (len(TEAMS[player.teamId]) - 1) * usernameSize[1]
                
                usernamePosition = (SIZE[0] - usernameSize[0]) // 2
                if player.teamId in TEAMS_POSITIONS:
                    usernamePosition = (SIZE[0] - usernameSize[0]) // 2 * TEAMS_POSITIONS[player.teamId]
                
                font_color = DEFAULT_LOBBY_COLOR
                
                if(player.username in readyPlayers):
                    font_color = READY_LOBBY_COLOR

                usernameSurface = pg.font.Font.render(usernameFont, usernameText, False, font_color.color)
                SCREEN.blit(usernameSurface, (usernamePosition, h))
        
        
        # Lights
        if DEBUG: # Draw lights where they are meant to be in the server
            pg.draw.rect(SCREEN, (255,255,0), [200*SCALE_FACTOR[0], 200*SCALE_FACTOR[1], 10, 10])
            pg.draw.rect(SCREEN, (255,255,0), [500*SCALE_FACTOR[0], 800*SCALE_FACTOR[1], 10, 10])
            pg.draw.rect(SCREEN, (255,255,0), [1500*SCALE_FACTOR[0], 500*SCALE_FACTOR[1], 10, 10])
        

        # Teams display
        if LOBBY:
            for id in TEAMS_NAMES:
                SCREEN.blit(TEAMS_TEXTS[id], (TEAMS_FINAL_POSITIONS[id], TEAM_DISPLAY_HEIGHT))
            
            TEAMS = {0 : [], 1 : [], 2 : []}
        
        
        # Ping
        pingText = "Ping : " + str(PING) + " ms"
        pingSize = pg.font.Font.size(pingFont, pingText)
        
        pingSurface = pg.font.Font.render(pingFont, pingText, False, WHITE.color)
        
        SCREEN.blit(pingSurface, (SIZE[0] - pingSize[0], 0))
        
        
        # Remaining game time
        if not LOBBY:
            timeText = "Remaining Seeking Time : " + str(GAME_TIME) + "s"
            timeSize = pg.font.Font.size(timeFont, timeText)
            
            timeSurface = pg.font.Font.render(timeFont, timeText, False, WHITE.color)
            
            SCREEN.blit(timeSurface, (TEAMS_FINAL_POSITIONS[0], TEAM_DISPLAY_HEIGHT))
        
        
        # In Transition state
        if IN_TRANSITION:
            transitionSize = pg.font.Font.size(transitionFont, TRANSITION_TEXT)
            
            transitionSurface = pg.font.Font.render(transitionFont, TRANSITION_TEXT, False, WHITE.color)
            
            SCREEN.blit(transitionSurface, ((SIZE[0] - transitionSize[0]) // 2, (SIZE[1] - transitionSize[1]) // 2))
        
        
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
        
        if (update(state)) : # request failed
            requestNumber+=1
        else :
            requestNumber=0
        
        if requestNumber>=MAX_REQUESTS:
            exitError("Max number of request has been passed for inputs!")

        
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
    
    message = send("CONNECT " + USERNAME + " END") # Should be "CONNECTED <Username> SIZE WALLS <WallsString> STATE <PlayersString> SHADES <ShadesString> END"
    
    if message!=None: messages = message.split(" ")
    else: messages=None
    
    if DEBUG:
        print("messages: ", messages)
    
    if (messages!=None and len(messages) == 10 and messages[0] == "CONNECTED" and messages[1] == USERNAME and messages[3] == "WALLS" and messages[5] == "LOBBY" and messages[7] == "STATE" and messages[9] == "END"):
        
        # get serveur default screen size
        try:
            sizeStr = "" + messages[2]
            sizeStr = sizeStr.replace("(", "")
            sizeStr = sizeStr.replace(")", "")
            
            sizeStr = sizeStr.split(",")
            
            SIZE = (int(sizeStr[0]), int(sizeStr[1]))
        except ValueError:
            if DEBUG:
                print("Size Error ! Size format was not correct !")
            SIZE = (400, 300)   # Some default size.
        
        # set walls players and shades
        update(messages[3] + " " + messages[4] + " " + messages[9]) # Walls
        update(messages[5] + " " + messages[6] + " " + messages[7] + " " + messages[8] + " " + messages[9]) #Players and Shades
        
        return True
    
    # Manage failed connections
    elif messages!=None and "CONNECTED" not in messages:
        askNewPseudo(message)
        
        global SOCKET
        
        SOCKET.close()
        SOCKET = None

    return False



def askNewPseudo(errorMessage:str):
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
        elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            return "INPUT " + USERNAME + " READY END"
    
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
        SOCKET = socket(AF_INET, SOCK_DGRAM)
        SOCKET.settimeout(SOCKET_TIMEOUT)
        try:
            SOCKET.connect((SERVER_IP, SERVER_PORT))
        except TimeoutError or ConnectionError:
            if DEBUG:
                traceback.print_exc()
            exitError("Connection attempt failed, retrying...")
            SOCKET=None
            
    # Usual behavior
    if SOCKET != None:
        t = time.time()

        # send data
        try:
            if DEBUG:
                print("input: ",input)
            SOCKET.sendall(bytes(input, "utf-8"))
        except (OSError):
            if DEBUG:
                traceback.print_exc()
            exitError("Loss connection with the remote server while sending data.")
            return
            
        # receive answer
        try:
            answer = str(SOCKET.recv(1024*16), "utf-8")
            if DEBUG:
                print("answer: ",answer)
             
            PING = int((time.time() - t) * 1000)
            
            return answer
        except (OSError):
            if DEBUG:
                traceback.print_exc()
            exitError("Loss connection with the remote server while receiving data.")
            return



def update(state="STATE [] END"):
    """Update the local variables representing the current state of the game from the given state.

    Args:
        state (str): The normalized state of the game. Defaults to "STATE [] END".
    Returns:
        bool: was there a problem in updating variables ?
    """
        
    global WALLS
    global PLAYERS
    global UNVISIBLE
    global readyPlayers
    global LOBBY
    global GAME_TIME
    global IN_TRANSITION
    global TRANSITION_TEXT

    if state == None or type(state) != str or state == "":
        return False
    
    messages = state.split(" ")
    
    ### Simple commands : KEYWORD <content> END
    
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
        readyPlayers = interp(messages[1], list=["", 0])["list"]
        IN_TRANSITION = False
        LOBBY = True
        return False
    
    elif len(messages) == 3 and messages[0] == "GAME" and messages[2] == "END":
        GAME_TIME = interp(messages[1], time=0.0)["time"]
        IN_TRANSITION = False
        LOBBY = False
        return False
    
    elif(len(messages) == 3 and messages[0] == "TRANSITION_GAME_LOBBY" and messages[2] == "END"):
        TRANSITION_TEXT = interp(messages[1], text="")["text"].replace("_", " ")
        IN_TRANSITION = True
        return False
    
    elif(len(messages) == 3 and messages[0] == "TRANSITION_LOBBY_GAME" and messages[2] == "END"):
        TRANSITION_TEXT = interp(messages[1], text="")["text"].replace("_", " ")
        IN_TRANSITION = True
        return False
    
    ### Concatenated commands
    
    else:
        # dictionary representing the known keywords and the number of parameters in <content> they take
        keywords = {"STATE" : 1, "WALLS" : 1, "SHADES" : 1, "LOBBY" : 1, "GAME" : 1, "TRANSITION_GAME_LOBBY" : 1, "TRANSITION_LOBBY_GAME" : 1}
        
        if len(messages) >= 3:
            conc = messages
            
            if conc[0] in keywords:
                # generate partial command
                command = conc[0] + " "
                
                n = keywords[conc[0]]
                
                for i in range(n):
                    command += conc[1 + i] + " "
                command += "END"
                
                conc[0:1 + n] = []
                
                m = len(conc)
                remains = ""
                for i in range(m):
                    if i != m - 1:
                        remains += conc[i] + " "
                    else:
                        remains += conc[i]
                
                return update(command) or update(remains)
            else:
                return True
            
        elif conc == ["END"]:
            return False
        
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
        if send("DISCONNECTION " + USERNAME + " END") == "DISCONNECTED " + USERNAME + " END":
            CONNECTED = False
            SOCKET.close()
            SOCKET = None
            break
        requestNumber+=1
    
    if requestNumber>=MAX_REQUESTS:
        exitError("Max number of request has been passed for disconnection!")


def exitError(errorMessage="Sorry a problem occured..."):
    """Exit the game
        Called if there has been a problem with the server
    Args:
        errorMessage (str): the string to print according to the error ("Sorry a problem occured..." by default)"""
        
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
        exitError("Max number of request has been passed for connections!")
    
    
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
