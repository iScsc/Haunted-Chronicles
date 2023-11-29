
from player import Player
from light import Light
from numpy import angle
from shapely.geometry import Polygon, Point
from shapely import get_coordinates, get_interior_ring,get_exterior_ring
import interpretor
from common import *


def extractCorner(p):
    x,y = p.position.x, p.position.y
    dx,dy = p.size.w, p.size.h
    BD = (x+dx,y+dy) # Corner down right
    BG = (x,y+dy) # Corner down left
    HG = (x,y) # Corner up left
    HD = (x+dx,y) # Corner up right
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
            return (lx,sizey)
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
    return (abs(px + (px - lx)*ty),wally)
    
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
    coord = [Borderj,corners[j],corners[i],Borderi]
    if nextCorner(pi[0],pi[1],sizex,sizey) == pj:
        coord.append(pi)
    else :
        while pj != pi:
            coord.append(pi)
            pi = nextCorner(pi[0],pi[1],sizex,sizey)
    
    if not(Polygon(coord).contains(Point(l.position.x,l.position.y))):
        return coord
    poly = Polygon([(0,0),(0,sizey),(sizex,sizey),(sizex,0)])
    shadows = poly.difference(Polygon(coord))
    return get_coordinates(shadows).tolist()

def OneSource(l,listOfp,sizex,sizey):
    poly = Polygon()
    for p in listOfp:
        body = Polygon(extractCorner(p))
        if not(body.contains(Point(l.position.x,l.position.y))):           
            polyp = Polygon(polyInLight(l,p,sizex,sizey))
            poly = poly.union(polyp)
        # else :
        #     print("light is inside an object")
    return(poly)

def AllSources(listOfl,listOfp,sizex,sizey,listShadows = []):
    poly = Polygon([(0,0),(0,sizey),(sizex,sizey),(sizex,0)])
    for i in range(len(listOfl)):
        polyl = OneSource(listOfl[i],listOfp,sizex,sizey)
        shadesI = polyl
        if i<len(listShadows):
            shadesI = listShadows[i].union(polyl)
        poly = poly.intersection(shadesI)
    return(poly)

def Visible(p,listOfl,listOfp,sizex,sizey,FixSources = Polygon(),listofWall = [],listShadows = []):
    l = Light(Position(p.position.x+p.size.h/2,p.position.y+p.size.w/2))
    listOfp2 = [x for x in listOfp if x!=p]
    poly = OneSource(l,listOfp2 + listofWall,sizex,sizey)
    shadowsFromPlayers = AllSources(listOfl,listOfp,sizex,sizey,listShadows)
    mobileSources = poly.union(shadowsFromPlayers)
    
    x,y = p.position.x-10, p.position.y-10
    dx,dy = p.size.w+20, p.size.h+20
    BD = (x+dx,y+dy)
    BG = (x,y+dy)
    HG = (x,y)
    HD = (x+dx,y)
    proximity = Polygon([BD,BG,HG,HD])
    return(mobileSources.union(FixSources).difference(proximity))

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
    
#    if type(shadows)==type(Polygon()):
#        listcoord = [[int(i) for i in x ] for x in get_coordinates(shadows).tolist()]
#        return "["+str(listcoord).replace("[","(").replace("]",")").replace(" ","")[1:-1]+"]"
    l = []
    endl = []
    startNotFound =True

    Geoms = []
    if type(shadows)==type(Polygon()):
        Geoms = extractGeoms(shadows)
    else :
        for p in shadows.geoms:
            Geoms += extractGeoms(p)
            

    for p in Geoms:
        l2 = [[int(i) for i in x ] for x in get_coordinates(p).tolist()]
        l+=l2
        if startNotFound:
            endl=[l2[0]]
            startNotFound = False
        l+= [l2[0]] + endl
    return "["+str(l+endl).replace("[","(").replace("]",")").replace(" ","")[1:-1]+"]"

def extractGeoms(poly):
    Geoms = []
    if type(poly)==type(Polygon()):
        Geoms.append(get_exterior_ring(poly))
        i = 0
        while i!=-1:
            p = get_interior_ring(poly,i) 
            if p!=None:
                i+=1
                Geoms.append(p)
            else:
                i= -1
    else:
        print("warning : wrong type of argument")
    return Geoms


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

    p00 = Player("","p00",position=Position(10,10),size=Size(20,20))
    p02 = Player("","p02",position=Position(10,70),size=Size(20,20))
    p20 = Player("","p20",position=Position(70,10),size=Size(20,20))
    p11 = Player("","p11",position=Position(50,50),size=Size(20,20))

    l = Light(Position(50,50))
    v = Visible(p11,[l],[p00,p02,p20],100,100)
    print(v)
    print(len(v.geoms))
    print(sendingFormat(v))
    
    poly0 = Polygon([(0,0),(0,3),(3,3),(3,0)])
    poly1 = Polygon([(1,1),(1,2),(2,2),(2,1)])


    p = poly0.difference(poly1)
    print(p)
    print(get_coordinates(p))
    print(str(p))
    print(sendingFormat(p))
    
