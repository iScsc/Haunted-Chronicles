class Color :
    
    def __init__(self,r=255,g=0,b=0):
        self.color=(r,g,b)
    
    def __str__(self):
        return str(self.color).replace(' ','')
    
    

class Position :
    
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    
    def __str__(self):
        return str((self.x,self.y)).replace(' ','')
        
    

class Size :
    
    def __init__(self,w=50,h=50):
        self.w=w
        self.h=h
    
    def __str__(self):
        return str((self.w,self.h)).replace(' ','')