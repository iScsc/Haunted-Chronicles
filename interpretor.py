import common



def spc(string):
    
    #getting parenthesis index
    po=[]
    pf=[]
    indexo=0
    indexf=0
    while indexo!=-1 and indexf!=-1:
        indexo=string.find('(',indexo)
        indexf=string.find(')',indexf)
        if (indexo!=-1 and indexf!=-1):
            if (len(pf)>0 and indexo<pf[-1]):
                pf[-1]=indexf
                indexf+=1
                indexo+=1
            else :
                po.append(indexo)
                indexo+=1
                pf.append(indexf)
                indexf+=1
    
    #getting substrings
    substr=[]
    if (len(po)==0):
        substr+=string.split(',')
    elif (po[0]!=0):
        substr+=(string[0:po[0]]).split(',')
    for i in range(len(po)):
        substr.append(string[po[i]+1:pf[i]])
        if (i<len(po)-1):
            substr+=(string[pf[i]+1:po[i+1]]).split(',')
    if (len(pf)>0 and pf[-1]!=len(string)-1):
        substr+=(string[pf[-1]+1:]).split(',')
        
    #epurating from void substring
    substr=[s for s in substr if s!='']
    
    return substr



def interp(playerString, **kwargs):
    
    from player import Player
    from wall import Wall
    
    values=spc(playerString)
    assert(len(values)==len(kwargs))
    
    i=0
    
    for arg in kwargs:
        
        if type(kwargs[arg])==str:
            kwargs[arg]=values[i]
            
        elif type(kwargs[arg])==int:
            kwargs[arg]=int(values[i])
            
        elif type(kwargs[arg])==float:
            kwargs[arg]=float(values[i])
            
        elif type(kwargs[arg])==common.Color:
            d=interp(values[i],r=0,g=0,b=0)
            kwargs[arg]=common.Color(d['r'],d['g'],d['b'])
            
        elif type(kwargs[arg])==common.Position:
            d=interp(values[i],x=0,y=0)
            kwargs[arg]=common.Position(d['x'],d['y'])
            
        elif type(kwargs[arg])==common.Size:
            d=interp(values[i],w=0,h=0)
            kwargs[arg]=common.Size(d['w'],d['h'])
            
        elif type(kwargs[arg])==Player:
            d=interp(values[i],username="",color=common.Color(),position=common.Position(),size=common.Size())
            kwargs[arg]=Player("",d['username'],d['color'],d['position'],d['size'])
            
        elif type(kwargs[arg])==Wall:
            d=interp(values[i],id=0,color=common.Color(),position=common.Position(),size=common.Size())
            kwargs[arg]=Wall(d['id'],d['color'],d['position'],d['size'])
        
        i+=1
    return kwargs