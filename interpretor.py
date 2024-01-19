import common
import math
from player import Player
from wall import Wall

### ----- String Parsing ----- ###

def spc(string:str, strip=False):
    """Splits a given string on parenthesis and commas, taking just into acount first level parenthesis.
    For instance: "(abc,def),ghi,(jkl,(mno))" -> ["abc,def","ghi","jkl,(mno)"]

    Args:
        string (str): The string to split
        strip (bool): The boolean representing if the values should be stripped from forbidden characters before being processed.

    Returns:
        list(str): The list of substrings 
    """
    
    #getting parenthesis index
    
    po=[] #list of opening parenthesis
    pf=[] #list of closing parenthesis
    indexo=0 #index of the last opening parenthesis found
    indexf=0 #index of the last closing parenthesis found
    
    # print("string =", string)
    forbidden_char = ["[", "]", "'", '"']
    
    if strip:
        if len(string) == 1 and string[0] in forbidden_char:
            string = ""
        while len(string) >= 2 and string[0] in forbidden_char:
            string = string[1:]
        while len(string) >= 2 and string[-1] in forbidden_char:
            string = string[:-1]
    
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
    substr=[s for s in substr if s not in ['',"'","['","']",'[',']','[]']]
    
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
            d=interp(values[i],teamId=0, username="",color=common.Color(),position=common.Position(),size=common.Size())
            # get rid of '' around usernames due to str(str)
            if len(d['username'])>2 and ((d['username'][0]=="'" and d['username'][-1]=="'") or (d['username'][0]=="\"" and d['username'][-1]=="\"")):
                d['username']=d['username'][1:-1]
            kwargs[arg]=Player(d['teamId'],d['username'],d['color'],d['position'],d['size'])
            
        elif type(kwargs[arg])==Wall:
            d=interp(values[i],id=0,color=common.Color(),position=common.Position(),size=common.Size())
            kwargs[arg]=Wall(d['id'],d['color'],d['position'],d['size'])
        
        # list, uses recursivity, shifts index
        elif type(kwargs[arg])==list:
            # kwargs[arg]=[a,k...]
            values = spc(string, True)
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


### ----- Byte Messages ----- ###

KEY=bytes("key","utf-16")

COMMANDS_TO_BYTES = {
    "CONNECT":bytes([0]),
    "INPUT":bytes([1]),
    "DISCONNECTION":bytes([2]),
    "CONNECTED":bytes([10]),
    "STATE":bytes([11]),
    "WALLS":bytes([12]),
    "SHADOWS":bytes([13]),
    "LOBBY":bytes([14]),
    "":bytes(0),
    "VARIABLE":bytes(1),
    "CONTINUE":bytes(2),
    "END":bytes(3)
    }

BYTES_TO_COMMAND = {
    bytes([0]):"CONNECT",
    bytes([1]):"INPUT",
    bytes([2]):"DISCONNECTION",
    bytes([10]):"CONNECTED",
    bytes([11]):"STATE",
    bytes([12]):"WALLS",
    bytes([13]):"SHADOWS",
    bytes([14]):"LOBBY",
    }

TYPES_TO_BYTES = {
    int:bytes([0]),
    float:bytes([1]),
    str:bytes([2]),
    bool:bytes([3]),
    list:bytes([10]),
    tuple:bytes([11]),
    Player:bytes([20]),
    Wall:bytes([21])
}

BYTES_TO_TYPE = {
    bytes([0]):int,
    bytes([1]):float,
    bytes([2]):str,
    bytes([3]):bool,
    bytes([10]):list,
    bytes([11]):tuple,
    bytes([20]):Player,
    bytes([21]):Wall
}

FLOAT_PRECISION=100

def byteMessage(command:str,listOfParam:list,end="END"):
    """Transforms a message into custom byte string

    Args:
        command (str): type of message, either "CONNECT", "INPUT", "DISCONNECTION", "CONNECTED", "STATE", "WALS", "SHADOWS" or "LOBBY"
        listOfParam (list): list of parameters linked to the type of the message
        end (str, optional): how this message ends. Defaults to "END".
    """
    
    byteMsg=bytes(0)
    
    byteMsg+=COMMANDS_TO_BYTES[command]
    
    for x in listOfParam:
        byteMsg=paramBytes(x)
    
    byteMsg+=COMMANDS_TO_BYTES[end]
    
    return byteMsg


def bytesParam(param):
    """Transform a variable into bytes

    Args:
        param (_type_): a variable
    """
    
    byteParam=bytes(0)
    byteParam+=TYPES_TO_BYTES[type(param)]
    
    
    # classic types
    
    if type(param)==int: 
        n=int(math.log(param,256))
        byteParam+=bytes([n])
        intl=[]
        for _ in range(n):
            intl.append(param%256)
            param//=256
        intl.reverse()
        byteParam+=bytes(intl)
        
    elif type(param)==float:
        byteParam+=bytesParam(int(param*FLOAT_PRECISION))[:-1]
    
    elif type(param)==bool:
        byteParam+=bytes([param])
        
    elif type(param)==str:
        byteParam+=bytes(param,"utf-8")    
            
    
    # common types
        
    elif type(param)==common.Color:
        byteParam+=bytes(param.color)
    
    elif type(param)==common.Position: #TODO
        byteParam+=bytes((param.x,param.y))
    
    elif type(param)==common.Size: #TODO
        byteParam+=bytes((param.h,param.w))
    
    
    # complex types
    
    elif type(param)==Player:
        byteParam+=bytesParam(param.teamId)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.username)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.color)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.position)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.size)
    
    elif type(param)==Wall:
            bytesParam(param.id)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.color)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.position)+COMMANDS_TO_BYTES["VARIABLE"]+\
            bytesParam(param.size)
    
    
    # list and tuples
    elif type(param)==list:
        for x in param:
            byteParam+=bytesParam(x)+COMMANDS_TO_BYTES["VARIABLE"]
        byteParam=byteParam[:-1]
    
    elif type(param)==tuple:
        for x in param:
            byteParam+=bytesParam(x)+COMMANDS_TO_BYTES["VARIABLE"]
        byteParam=byteParam[:-1]
        
    byteParam+=COMMANDS_TO_BYTES["VARIABLE"]


def messageBytes(byteMsg:bytes):
    """gets the message from a byte string

    Args:
        byteMsg (bytes): a byte string
    """
    
    temp=byteMsg
    
    message=[]
    
    message.append(BYTES_TO_COMMAND[temp[0:1]])
    temp=temp[1:]
    
    while temp!=bytes(0):
        x,temp=paramBytes(temp)
        message.append(x)
    
    return message


def paramBytes(byteParam:bytes):
    """gets the first parameter from a formatted bytes string

    Args:
        byteParam (bytes): a formatted byte string

    Returns:
        tuple[Any|bytes]: the parameter and the bytes left
    """
    
    paramType=BYTES_TO_TYPE[byteParam[0:1]]
    temp=byteParam[1:]
    
    # classic types
    
    if paramType==int:
        param:int=0
        n=temp[0]
        temp=temp[1:]
        var,temp=extractVariable(temp,min=n)
        for i in range(n):
            param*=256
            param+=var[i]
        return param, temp
        
    elif paramType==float:
        fparam:float
        fparam,temp=paramBytes(temp)
        fparam/=FLOAT_PRECISION
        return fparam,temp
    
    elif paramType==bool:
        return bool(var[0]), temp
        
    elif paramType==str:
        param:str=str(param,"utf-8")    
        return param, temp
            
    
    # common types
        
    elif paramType==common.Color:
        r,temp=paramBytes(temp)
        g,temp=paramBytes(temp)
        b,temp=paramBytes(temp)
        return common.Color(r,g,b),temp
    
    elif paramType==common.Position:
        x,temp=paramBytes(temp)
        y,temp=paramBytes(temp)
        return common.Position(x,y),temp
    
    elif paramType==common.Size:
        w,temp=paramBytes(temp)
        h,temp=paramBytes(temp)
        return common.Size(w,h),temp
    
    
    # complex types
    
    elif paramType==Player:            
        teamID,temp=paramBytes(temp)
        username,temp=paramBytes(temp)
        color,temp=paramBytes(temp)
        position,temp=paramBytes(temp)
        size,temp=paramBytes(temp)
        return Player(teamID,username,color,position,size),temp
    
    elif paramType==Wall:     
        id,temp=paramBytes(temp)
        color,temp=paramBytes(temp)
        position,temp=paramBytes(temp)
        size,temp=paramBytes(temp)
        return Wall(id,color,position,size), temp
    
    
    # list and tuples
    elif paramType==list:
        l=[]
        n=temp[0]
        temp=temp[1:]
        for _ in range(n):
            var,temp=paramBytes(temp)
            l.append(var)
        return l,temp
    
    elif paramType==tuple:
        l=[]
        n=temp[0]
        temp=temp[1:]
        for _ in range(n):
            var,temp=paramBytes(temp)
            l.append(var)
        return tuple(l),temp


def extractVariable(byteVar:bytes,min=1):
    """extract a variable from a byte string (up to a null byte after a min nbr of bytes)

    Args:
        byteVar (bytes): a formatted byte string
        min (int, optional): the minimum number of bytes. Defaults to 1.

    Returns:
        tuple[Any,bytes]: a variable and the bytes left
    """
    
    res=bytes(0)
    i=0
    while i<min or byteVar[i:i+1]!=COMMANDS_TO_BYTES["VARIABLE"]:
        res+=byteVar[i:i+1]
    return res, byteVar[i+1:]
    

def splitCommand(byteMessage:bytes):
    """split a byte message into byte commands

    Args:
        byteMessage (bytes): a formatted byte string

    Returns:
        list[bytes]: the list of byte commands
    """
    commands=[]
    temp=byteMessage
    while temp != bytes(1):
        command,temp=extractCommand(temp)
        commands.append(command)
    return commands


def extractCommand(byteMessage:bytes):
    """extract a single command from a formatted byte string cntaining concatenated commands

    Args:
        byteMessage (bytes): a formatted byte string

    Returns:
        tuple[bytes,bytes]: the byte command and the left bytes
    """
    fstNull=False
    temp=byteMessage
    command=bytes(0)
    while not fstNull or temp[0]!=0:
        if fstNull:
            command+=COMMANDS_TO_BYTES["VARIABLE"]+temp[0:1]
            fstNull=False
        elif temp[0]==0:
            fstNull=True
        else:
            command+=temp[0:1]
        temp=temp[1:]
    command+=COMMANDS_TO_BYTES["END"]
    return command, temp[1:]