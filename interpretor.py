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
                print(pf)
                print(indexf)
                pf[-1]=indexf
                indexf+=1
                indexo+=1
            else :
                po.append(indexo)
                indexo+=1
                pf.append(indexf)
                indexf+=1
    print(po)
    print(pf)
    
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
        substr+=(string[pf[-1]:]).split(',')
        
    #epurating from void substring
    substr=[s for s in substr if s!='']
    
    return substr

def interp(playerString, **kwargs):
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
        
        i+=1
    return kwargs