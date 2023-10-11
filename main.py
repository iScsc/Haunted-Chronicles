import pygame as pg
import sys
import time

import asyncio
import socketserver

from server import MyTCPHandler
from displayer import Displayer

def gn():
    time.sleep(1)
    print("Waited.")

async def main():
    FPS = 60

    s = Displayer()
    c = pg.time.Clock()
    i = 0
    
    # Create the server, binding to localhost on port 9998
    while True:
        
        events = pg.event.get()
        
        for event in events:
            if event.type == pg.QUIT:
                sys.exit()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE or event.key == pg.K_q:
                    sys.exit()
        
        s.baseDisplay(i)
        c.tick(FPS)
        await asyncio.to_thread(gn)
        i += 1
        i %= 600

if __name__ == "__main__":
    asyncio.run(main())
