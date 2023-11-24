import common



def spc(string:str):
    """Splits a given string on parenthesis and commas, taking just into acount first level parenthesis.
    For instance: "(abc,def),ghi,(jkl,(mno))" -> ["abc,def","ghi","jkl,(mno)"]

    Args:
        string (str): The string to split

    Returns:
        list(str): The list of substrings 
    """
    
    #getting parenthesis index
    
    po=[] #list of opening parenthesis
    pf=[] #list of closing parenthesis
    indexo=0 #index of the last opening parenthesis found
    indexf=0 #index of the last closing parenthesis found
    
    while indexo!=-1 and indexf!=-1: # While an opening and closing parenthesis have been found
        indexo=string.find('(',indexo) # find the next  parethesis index starting from the last one
        indexf=string.find(')',indexf)
        if (indexo!=-1 and indexf!=-1): # If an opening and closing parenthesis have been found
            if (len(pf)>0 and indexo<pf[-1]): # If the situation is "...(...(...)...)..." the new opening parenthesis is a lower level one
                pf[-1]=indexf # last closing parenthesis was a lower level one (inside other parenthesis) and should not be taken into account
                indexf+=1
                indexo+=1
            else : # first level parenthesis
                po.append(indexo)
                indexo+=1
                pf.append(indexf)
                indexf+=1
    
    #getting substrings
    
    substr=[] # list of substrings to be returned
    
    if (len(po)==0): # no parenthesis found: split the string only on commas
        substr+=string.split(',')
        
    elif (po[0]!=0): # take the begining of the string (before the first parenthesis) and split it on commas 
        substr+=(string[0:po[0]]).split(',')
        
    for i in range(len(po)): # for each pair of '(' ')', gets what's inbetween
        substr.append(string[po[i]+1:pf[i]])
        if (i<len(po)-1): # gets what's inbetween pairs and split it on commas
            substr+=(string[pf[i]+1:po[i+1]]).split(',')
            
    if (len(pf)>0 and pf[-1]!=len(string)-1): # take the end of the string (after the first parenthesis) and split it on commas
        substr+=(string[pf[-1]+1:]).split(',')
        
    #epurating from void substring, residual apostrophe and unwanted substrings
    substr=[s for s in substr if s not in ['',"'","['","']",'[',']']]
    
    return substr



def interp(string, **kwargs):
    """Interprets a given string according to the specification in **kwargs
    
    Supported types are:
        int, float, str, Color, Position, Size, Player, Wall, list and tuple

    Args:
        string (str): The string to interpret.
        **kwargs (dict[str|Any]): kwargs should match the type of the desired variable.
            Ex: for an int i of value a one shoulde use "interp('a',i=0)"
    
    Special cases:
    
        list: interp("[...]", list=[a,i]) where a matches the type of the list elements and i is the number of elements to look for.
            or list=[a,0] when all substrings match the a structure, should be the last kwarg
            or list=[None,-1,...] where ... matches the type of elements one by one
            edge effect
        
        tuple: interp("(...)", tuple=(a,i)) see list (no edge effect)

    Returns:
        dict[str|Any]: updated kwargs
    """
    
    # local imports to avoid circular imports
    from player import Player
    from wall import Wall
    
    # splits the given string
    values=spc(string)
    
    # current index
    i=0
    
    for arg in kwargs:
        
        # basic types 
        if type(kwargs[arg])==str:
            kwargs[arg]=values[i]
            
        elif type(kwargs[arg])==int:
            kwargs[arg]=int(values[i])
            
        elif type(kwargs[arg])==float:
            kwargs[arg]=float(values[i])
        
        # common types, uses recursivity
        elif type(kwargs[arg])==common.Color:
            d=interp(values[i],r=0,g=0,b=0)
            kwargs[arg]=common.Color(d['r'],d['g'],d['b'])
            
        elif type(kwargs[arg])==common.Position:
            d=interp(values[i],x=0,y=0)
            kwargs[arg]=common.Position(d['x'],d['y'])
            
        elif type(kwargs[arg])==common.Size:
            d=interp(values[i],w=0,h=0)
            kwargs[arg]=common.Size(d['w'],d['h'])
        
        # specific types, uses recursivity
        elif type(kwargs[arg])==Player:
            d=interp(values[i],username="",color=common.Color(),position=common.Position(),size=common.Size())
            kwargs[arg]=Player("",d['username'],d['color'],d['position'],d['size'])
            
        elif type(kwargs[arg])==Wall:
            d=interp(values[i],id=0,color=common.Color(),position=common.Position(),size=common.Size())
            kwargs[arg]=Wall(d['id'],d['color'],d['position'],d['size'])
        
        # list, uses recursivity, shifts index
        elif type(kwargs[arg])==list:
            # kwargs[arg]=[a,k...]
            k=kwargs[arg][1]
            if k==-1:
                k=len(kwargs[arg])-2
                for j in range(k):
                    d=interp('('+values[i+j]+')',element=kwargs[arg][2+j])
                    kwargs[arg][2+j]=d['element']
            elif k==0:
                k=len(values)-i
                for j in range(k):
                    d=interp('('+values[i+j]+')',element=kwargs[arg][0])
                    kwargs[arg].append(d['element'])
            else :
                for j in range(k):
                    d=interp('('+values[i+j]+')',element=kwargs[arg][0])
                    kwargs[arg].append(d['element'])
            i+=k # shift current index
            del kwargs[arg][0] # removes a from the list
            del kwargs[arg][0] # removes k from the list
            
        # tuple, uses recursivity
        elif type(kwargs[arg])==tuple:
            d=interp(values[i],list=list(kwargs[arg]))
            kwargs[arg]=tuple(d['list'])
        
        i+=1
        
    return kwargs