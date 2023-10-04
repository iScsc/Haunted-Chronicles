import pygame as pg

class Displayer:
    BLACK = 0, 0, 0
    RED = 255, 0, 0
    LENGTH = 100
    SCREEN_SIZE = (800, 800)
    
    def __init__(self):
        self.screen = pg.display.set_mode(Displayer.SCREEN_SIZE)
        self.screen.fill(Displayer.BLACK)
        pg.display.update()
    
    def baseDisplay(self, i):
        self.screen.fill(Displayer.BLACK)
        pg.draw.rect(self.screen, Displayer.RED, [(100 + i, 100), (200, 200 + i)])
        pg.display.update()
    
    # pos = (400, 400)
