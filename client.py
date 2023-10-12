# ----------------------- Imports -----------------------
import pygame as pg
from threading import *

from socket import *

import time

from player import Player

# ----------------------- Variables -----------------------

SERVER_IP = "10.188.222.194" #"localhost"
SERVER_PORT = 9998
CONNECTED = False
DISCONNECTION_WAITING_TIME = 5

FPS = 60

SIZE = None
SCREEN = None

USERNAME = "John"
PLAYERS = []

WAITING_TIME = 0.01 # in seconds
TIMEOUT = 10 # in seconds

PING = None # in milliseconds

# ----------------------- Threads -----------------------

def display():
    """Thread to display the current state of the game given by the server.
    """
    
    global SCREEN
    global PLAYERS
    
    clock = pg.time.Clock()
    
    while CONNECTED:
        
        SCREEN.fill((0, 0, 0))  # May need to be custom
        
        for player in PLAYERS:
            pg.draw.rect(SCREEN, player.color, [player.position, player.size])
        
        pg.display.update()
        
        clock.tick(FPS)



def game():
    """Thread to send inputs to the server, receive the current state of the game from it, and update the client-side variables.
    """
    
    global PLAYERS
    global SERVER_IP
    global SERVER_PORT
    
    clock = pg.time.Clock()
    
    while CONNECTED:
        
        inputs = getInputs()
        
        state = send(inputs)
        
        update(state)
        
        clock.tick(FPS)



# ----------------------- Functions -----------------------

def connect():
    """Try to connect to the given SERVER_IP and SERVER_PORT. When successful, initialize the current state of the game.

    Returns:
        bool: is the connection successful ?
    """
    
    global SIZE
        
    message = send("CONNECT " + USERNAME + " END")
    
    messages = message.split(" ")
    
    if messages[0] == "CONNECTED" and messages[1] == USERNAME and messages[3] == "STATE":
        try:
            sizeStr = "" + messages[2]
            sizeStr = sizeStr.replace("(", "")
            sizeStr = sizeStr.replace(")", "")
            
            sizeStr = sizeStr.split(",")
            
            SIZE = (int(sizeStr[0]), int(sizeStr[1]))
        except:
            print("Size Error ! Size format was not correct !")
            SIZE = (400, 300)   # Some default size.
        
        beginIndex = len(messages[0]) + len(messages[1]) + len(messages[2]) + 3 # 3 characters 'space'
        update(message[beginIndex - 1:])
        
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
        print("Ping (ms) = ", PING)
        
        return answer



def update(state="STATE [] END"):
    """Update the local variables representing the current state of the game from the given state.

    Args:
        state (str): The normalized state of the game. Defaults to "STATE [] END".
    """
    
    global PLAYERS
    
    messages = state.split(" ")
    if len(messages) == 3 and messages[0] == "STATE" and messages[2] == "END":
        PLAYERS = Player.toPlayers(messages[1])



def exit():
    """Send the normalized disconnection request and then exits the game.
    """
    
    global CONNECTED
    
    t = time.time()
    while time.time() - t < DISCONNECTION_WAITING_TIME:
        if send("DISCONNECTION " + USERNAME + " END") == "DISCONNECTED " + USERNAME + " END":
            break
    
    CONNECTED = False
    #sys.exit()



def main():
    """Main function launching the parallel threads to play the game and communicate with the server.
    """
    
    global CONNECTED
    
    while not CONNECTED:
        CONNECTED = connect()
        time.sleep(WAITING_TIME)
    
    pg.init()
    
    global SCREEN
    SCREEN = pg.display.set_mode(SIZE)
    
    gameUpdater = Thread(target=game)
    displayer = Thread(target=display)
    
    gameUpdater.start()
    displayer.start()



# ----------------------- Client Side -----------------------

if __name__ == "__main__":
    
    print("Which username do you want to use ? (By default, it is " + USERNAME + ")")
    username = input()
    
    if username != "":
        USERNAME = username
    
    main()
