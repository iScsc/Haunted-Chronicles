
from player import Player
from light import Light
from numpy import angle
from shapely.geometry import Polygon
import time


def extractCorner(p):
    x,y = p.position
    dx,dy = p.size
    BD = (x+dx,y-dy)
    BG = (x-dx,y-dy)
    HG = (x-dx,y+dy)
    HD = (x+dx,y+dy)
    return [BD,BG,HG,HD]

def extremePoint(l,p):
    Corners = extractCorner(p)
    L = l.position
    maxphi = 0,0,0
    for i in range(4):
        for j in range(i,4):
            x1 = Corners[i][0] - l.position[0]
            y1 = Corners[i][1] - l.position[1]
            x2 = Corners[j][0] - l.position[0]
            y2 = Corners[j][1] - l.position[1]
            
            
            if x1 == 0 and y1 == 0:
                phi = 0
            else :
                phi = abs(angle((x2 + y2*1j)/(x1 + y1*1j)))

            if phi>maxphi[0]:
                maxphi = phi,i,j
                
    return(maxphi)

def pointBorder(l,point,sizex,sizey):
    lx,ly = l.position
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
        return (wallx,py + (py - ly)*tx)
    return (px + (px - ly)*ty,wally)
    
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
    if p.position[0] < l.position[0]:
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
        polyp = Polygon(polyInLight(l,p,sizex,sizey))
        poly = poly.union(polyp)
    return(poly)

def AllSources(listOfl,listOfp,sizex,sizey):
    poly = Polygon([(0,0),(0,sizey),(sizex,sizey),(sizex,0)])
    for l in listOfl:
        polyl = OneSource(l,listOfp,sizex,sizey)
        poly = poly.intersection(polyl)
    return(poly)

def Visible(p,listOfl,listOfp,sizex,sizey):
    l = Light(p.position)
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
        


### Tests and debug

if __name__ == "__main__":

    p00 = Player(ip="", username="p00", color=(0,0,0), position=(20,20), size=[10, 10])
    l = Light((50,50))
    l2 = Light((100,0))

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
    print(isVisible(v,p20))


