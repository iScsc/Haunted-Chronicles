# ----------------------- Imports -----------------------
import sys
import pygame as pg
from threading import *

from socket import *

import time

from player import Player
from wall import Wall

# ----------------------- Variables -----------------------
SERVER_IP = "192.168.1.34" #"localhost"
SERVER_PORT = 9998
CONNECTED = False
DISCONNECTION_WAITING_TIME = 5 # in seconds, time waited before disconnection without confirmation from the host
MAX_REQUESTS = 10 # number of requests without proper response before force disconnect

FPS = 60

SIZE = None
SCREEN = None

FONT = "Arial" # Font used to display texts
FONT_SIZE_USERNAME = 25
FONT_SIZE_PING = 12

USERNAME = "John"
PLAYERS = []
WALLS = []

WAITING_TIME = 0.01 # in seconds - period of connection requests when trying to connect to the host

PING = None # in milliseconds - ping with the server, None when disconnected

# ----------------------- Threads -----------------------

def display():
    """Thread to display the current state of the game given by the server.
    """
    
    global SCREEN
    global PLAYERS
    
    pg.init()
    
    SCREEN = pg.display.set_mode(SIZE)
    pingFont = pg.font.SysFont(FONT, FONT_SIZE_PING)
    usernameFont = pg.font.SysFont(FONT, FONT_SIZE_USERNAME)
    
    clock = pg.time.Clock()
    
    while CONNECTED:
        
        SCREEN.fill((0, 0, 0))  # May need to be custom
        
        pg.event.pump() # Useless, just to make windows understand that the game has not crashed...
        
        # Walls
        for wall in WALLS:
            pg.draw.rect(SCREEN, wall.color, [wall.position, wall.size])
        
        # Players
        for player in PLAYERS:
            pg.draw.rect(SCREEN, player.color.color, [player.position.x, player.position.y, player.size.w, player.size.h])
            
            usernameText = player.username
            usernameSize = pg.font.Font.size(usernameFont, usernameText)
            usernameSurface = pg.font.Font.render(usernameFont, usernameText, False, player.color.color)
            
            SCREEN.blit(usernameSurface, (player.position.x + (player.size.w - usernameSize[0]) // 2, player.position.y - usernameSize[1]))
        
        
        # Ping
        pingText = "Ping : " + str(PING) + " ms"
        pingSize = pg.font.Font.size(pingFont, pingText)
        
        pingSurface = pg.font.Font.render(pingFont, pingText, False, (255, 255, 255))
        
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
            exitError()

        
        clock.tick(FPS)
        



# ----------------------- Functions -----------------------

def connect():
    """Try to connect to the given SERVER_IP and SERVER_PORT. When successful, initialize the current state of the game.

    Returns:
        bool: is the connection successful ?
    """
    
    global SIZE
        
    message = send("CONNECT " + USERNAME + " END") # Should be "CONNECTED <Username> SIZE WALLS <WallsString> STATE <PlayersString> END"
    
    messages = message.split(" ")
    
    if messages[0] == "CONNECTED" and messages[1] == USERNAME and messages[3] == "WALLS" and messages[5] == "STATE" and messages[7] == "END":
        try:
            sizeStr = "" + messages[2]
            sizeStr = sizeStr.replace("(", "")
            sizeStr = sizeStr.replace(")", "")
            
            sizeStr = sizeStr.split(",")
            
            SIZE = (int(sizeStr[0]), int(sizeStr[1]))
        except:
            print("Size Error ! Size format was not correct !")
            SIZE = (400, 300)   # Some default size.
        
        beginWallIndex = len(messages[0]) + len(messages[1]) + len(messages[2]) + 3 # 3 characters 'space'
        beginPlayerIndex = len(messages[0]) + len(messages[1]) + len(messages[2]) + len(messages[3]) + len(messages[4]) + 5 # 5 characters 'space'
        
        update(message[beginWallIndex : beginPlayerIndex - 1] + " END") # Walls
        update(message[beginPlayerIndex:]) # Players
        
        return True

    return False



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
        return "INPUT " + USERNAME + " L END"
    elif keys[pg.K_RIGHT] or keys[pg.K_d]:
        return "INPUT " + USERNAME + " R END"
    elif keys[pg.K_UP] or keys[pg.K_z]:
        return "INPUT " + USERNAME + " U END"
    elif keys[pg.K_DOWN] or keys[pg.K_s]:
        return "INPUT " + USERNAME + " D END"
    
    return "INPUT " + USERNAME + " . END"



def send(input="INPUT " + USERNAME + " . END"):
    """Send a normalized request to the server and listen for the normalized answer.

    Args:
        input (str): Normalized request to send to the server. Defaults to "INPUT <Username> . END".

    Returns:
        str: the normalized answer from the server.
    """
    
    global PING
    
    with socket(AF_INET, SOCK_STREAM) as sock:
        t = time.time()
        
        # send data
        sock.connect((SERVER_IP, SERVER_PORT))
        sock.sendall(bytes(input, "utf-16"))
        
        
        # receive answer
        answer = str(sock.recv(1024*2), "utf-16")
        
        PING = int((time.time() - t) * 1000)
        
        return answer



def update(state="STATE [] END"):
    """Update the local variables representing the current state of the game from the given state.

    Args:
        state (str): The normalized state of the game. Defaults to "STATE [] END".
    """
    
    global WALLS
    global PLAYERS
    
    messages = state.split(" ")

    if len(messages) == 3 and messages[0] == "WALLS" and messages[2] == "END":
        WALLS = Wall.toWalls(messages[1])
    
    elif len(messages) == 3 and messages[0] == "STATE" and messages[2] == "END":
        players = Player.toPlayers(messages[1])
        if (players != None):
            PLAYERS=players
            return False
        else: return True
    return True



def exit():
    """Send the normalized disconnection request and then exits the game.
    """
    
    global CONNECTED
    requestNumber=0
    
    t = time.time()
    while time.time() - t < DISCONNECTION_WAITING_TIME and requestNumber<MAX_REQUESTS:
        requestNumber+=1
        if send("DISCONNECTION " + USERNAME + " END") == "DISCONNECTED " + USERNAME + " END":
            break
    
    if requestNumber>=MAX_REQUESTS:
        exitError()
    
    CONNECTED = False

def exitError():
    """Exit the game
        Called if there has been a problem with the server"""
        
    global CONNECTED
    
    print("Sorry a problem occured...")
    
    CONNECTED=False



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
