
from player import Player
from light import Light
from numpy import angle
from shapely.geometry import Polygon, Point
from shapely import get_coordinates
import time
import interpretor
from common import *


DEBUG = True

def extractCorner(p):
    x,y = p.position.x, p.position.y
    dx,dy = p.size.w, p.size.h
    BD = (x+dx,y+dy)
    BG = (x,y+dy)
    HG = (x,y)
    HD = (x+dx,y)
    return [BD,BG,HG,HD]

def extremePoint(l,p):
    Corners = extractCorner(p)
    maxphi = 0,0,0
    for i in range(4):
        for j in range(i,4):
            x1 = Corners[i][0] - l.position.x
            y1 = Corners[i][1] - l.position.y
            x2 = Corners[j][0] - l.position.x
            y2 = Corners[j][1] - l.position.y
            
            
            if x1 == 0 and y1 == 0:
                phi = 0
            else :
                phi = abs(angle((x2 + y2*1j)/(x1 + y1*1j)))

            if phi>maxphi[0]:
                maxphi = phi,i,j
                
    return(maxphi)

def pointBorder(l,point,sizex,sizey):
    lx,ly = l.position.x, l.position.y
    px,py = point
    wallx = 0
    wally = 0
    
    # tx represent the amount of time needed to reach the wall x
    
    if lx > px: # tx is positive
        tx = px/(lx-px)
    elif lx < px:
        tx = (sizex - px)/(px - lx)
        wallx = sizex
    else:
        if py>ly:
            return (lx,sizex)
        return (lx,0)
    
    if ly > py: # ty is positive
        ty = py/(ly-py)
    elif ly < py:
        ty = (sizey - py)/(py - ly)
        wally = sizey
    else:
        return (wallx,ly)
    
    if tx < ty:
        return (wallx,abs(py + (py - ly)*tx))
    return (abs(px + (px - ly)*ty),wally)
    
def nextCorner(x,y,sizex,sizey):
    if (x,y) == (0,0):
        return 0,sizey
    if (x,y) == (0,sizey):
        return sizex,sizey
    if (x,y) == (sizex,sizey):
        return sizex,0
    if (x,y) == (sizex,0):
        return 0,0

def cornerRight(x,y,sizex,sizey):
    if x==0:
        return 0,sizey
    if x==sizex:
        return sizex,0
    if y==0:
        return 0,0
    return sizex,sizey    

def polyInLight(l,p,sizex,sizey):
    phi,i,j = extremePoint(l,p)
    if p.position.x < l.position.x:
        i,j = j,i
    corners = extractCorner(p)
    Borderi = pointBorder(l,corners[i],sizex,sizey)
    Borderj = pointBorder(l,corners[j],sizex,sizey)
    xi,yi = Borderi
    pi = cornerRight(xi,yi,sizex,sizey)
    xj,yj = Borderj
    pj = cornerRight(xj,yj,sizex,sizey)
    coord = [Borderi,corners[i],corners[j],Borderj]
    while pj != pi:
        coord.append(pj)
        pj = nextCorner(pj[0],pj[1],sizex,sizey)
    return coord

def OneSource(l,listOfp,sizex,sizey):
    poly = Polygon()
    for p in listOfp:
        body = Polygon(extractCorner(p))
        if not(body.contains(Point(l.position.x,l.position.y))):           
            polyp = Polygon(polyInLight(l,p,sizex,sizey))
            poly = poly.union(polyp)
        else :
            print("light in")
    return(poly)


def AllSources(listOfl,listOfp,sizex,sizey):
    poly = Polygon([(0,0),(0,sizey),(sizex,sizey),(sizex,0)])
    for l in listOfl:
        polyl = OneSource(l,listOfp,sizex,sizey)
        if DEBUG:
            print("position light :",l.position,", polygon inlight :",polyl)
        poly = poly.intersection(polyl) # TODO error with Self-Intersection
    return(poly)

def Visible(p,listOfl,listOfp,sizex,sizey):
    l = Light(p.position) # TODO middle rather than top left corner
    listOfp2 = [x for x in listOfp if x!=p]
    poly = OneSource(l,listOfp2,sizex,sizey)
    return(poly.union(AllSources(listOfl,listOfp,sizex,sizey)))

def isVisible(shadows,p):
    body = Polygon(extractCorner(p))
    return not(shadows.contains_properly(body))

def allVisiblePlayer(shadows,listOfp):
    l = []
    for p in listOfp:
        if isVisible(shadows,p):
            l.append(p.username)
    return l
        
def sendingFormat(shadows):
    return "["+str(get_coordinates(shadows).tolist()).replace("[","(").replace("]",")").replace(" ","")[1:-1]+"]"

def toVisible(visibleString,DEBUG):
    try :
        visibleList = []
        
        string=interpretor.spc(visibleString)
        
        for s in string:
            visibleList.append(interpretor.interp(s,liste=[0.,2])['liste'])

        return visibleList
        
    except Exception as e:
        if DEBUG:
            print(e)
        return None



### Tests and debug

if __name__ == "__main__":

    p = Player("","John",position=Position(600,600),size=Size(20,20))
    l = Light(Position(864,486))
    v = Visible(p,[l],[p],864*2,486*2)
    print(sendingFormat(v))

    """
    p00 = Player(ip="", username="p00", color=(0,0,0), position=(20,20), size=[10, 10])
    l = Light(Position(50,50))
    l2 = Light(Position(100,0))

    print(extremePoint(l,p00))

    print(pointBorder(l,(30,10),200,200))
    print(pointBorder(l,(10,30),200,200))

    print(nextCorner(100,0,100,100))

    print(polyInLight(l,p00,100,100))

    p22 = Player(ip="", username="", color=(0,0,0), position=(80,80), size=[10, 10])
    print(polyInLight(l,p22,100,100))

    p20 = Player(ip="", username="p20", color=(0,0,0), position=(80,20), size=[10, 10])
    print(polyInLight(l,p20,100,100))

    p02 = Player(ip="", username="", color=(0,0,0), position=(20,80), size=[10, 10])
    print(polyInLight(l,p02,100,100))
    

    p10 = Player(ip="", username="p10", color=(0,0,0), position=(50,20), size=[10, 10])
    print(polyInLight(l,p10,100,100))

    p12 = Player(ip="", username="", color=(0,0,0), position=(50,80), size=[10, 10])
    print(polyInLight(l,p12,100,100))

    p01 = Player(ip="", username="", color=(0,0,0), position=(20,50), size=[10, 10])
    print(polyInLight(l,p01,100,100))

    p21 = Player(ip="", username="", color=(0,0,0), position=(80,50), size=[10, 10])
    print(polyInLight(l,p21,100,100))
    
    p11 = Player(ip="", username="p11", color=(0,0,0), position=(50,50), size=[10, 10])
    print(polyInLight(l,p21,100,100))
    
    print(OneSource(l,[p00,p10],100,100))
    print(OneSource(l2,[p00,p10],100,100))

    print(AllSources([l,l2],[p00,p10],100,100))
    #print(extractPoly(AllSources([l,l2],[p00,p10],100,100)))

    print("test 1")
    t1 = time.time()
    v = Visible(p00,[l,l2],[p00,p10],100,100)
    avp = allVisiblePlayer(v,[p00,p10,p20])
    t2 = time.time()
    print(t2-t1)
    
    print(v)
    print(str(v))
    print(isVisible(v,p20))
    print(avp)

    print("test 2")
    v = Visible(p00,[l,l2],[p00,p22,p21,p02],100,100)
    print(v)
    print(get_coordinates(v).tolist())
    print(isVisible(v,p20))
    
    print(OneSource(l,[p11,p10],100,100))

    print("--------------- test 3")
    v = Visible(p00,[l],[p00],100,100)
    print(v)
    print(get_coordinates(v).tolist())
    print(isVisible(v,p20))

    print("--------------- test 4")
    v = Visible(p00,[l],[p00,p22],100,100)
    print(v)
    print(get_coordinates(v).tolist())
    print(isVisible(v,p20))

    print("--------------- test 5")
    v = Visible(p00,[l],[p00,p02,p22],100,100)
    print(v)
    print(sendingFormat(v))
    print(isVisible(v,p20))
"""