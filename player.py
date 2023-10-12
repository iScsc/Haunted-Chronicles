class Player:
    
    BASE_COLOR = (255, 0, 0)
    BASE_POSITION = (0, 0)
    BASE_SIZE = (50, 50)
    
    def __init__(self, ip="", username="", color=(0,0,0), position=(0,0), size=[10, 10]):
        self.ip = ip
        self.username = username
        self.color = color
        self.position = position
        self.size = size
    
    
    
    def toString(self):
        msg = "(" + str(self.username) + "," + str(self.color) + "," + str(self.position) + "," + str(self.size) + ")"
        return msg.replace(" ", "")



    def toPlayers(playersString):
        
        playersList = []
        
        currentExtract = None
        
        onUsername, onColor, onPosition, onSize = False, False, False, False
        change = False # spot change of field in multiple fields variables
        error = False # spot errors in fields
        
        for c in playersString:
            
            #print(currentExtract)
            #print(onUsername, onColor, onPosition, onSize)
            #print(change, error)
            
            
            
            # --------------- Username ---------------
            if onUsername:
                
                if c != ",":
                    if len(currentExtract) == 0:
                        currentExtract.append(c)
                    else:
                        currentExtract[0] += c
                
                else:
                    onColor = True
                    onUsername, onPosition, onSize = False, False, False
                    change, error = False, False
            
            
            
            # --------------- Color ---------------
            elif onColor:
                
                if c == "(" and not error:
                    currentExtract.append([])
                    change = False
                
                elif c == ",":
                    
                    if not change and not error:
                        
                        try:
                            currentExtract[1][-1] = int(currentExtract[1][-1])
                            change = True
                        except:
                            error = True
                            change = False
                            currentExtract[1] = Player.BASE_COLOR
                    
                    elif change:
                        change = False
                        onPosition = True
                        onUsername, onColor, onSize = False, False, False
                        change, error = False, False
                
                elif c == ")":
                    
                    if not error:
                        try:
                            currentExtract[1][-1] = int(currentExtract[1][-1])
                        except:
                            error = True
                            currentExtract[1] = Player.BASE_COLOR
                    
                    change = True
                
                elif not error:
                    if len(currentExtract[1]) == 0 or change:
                        currentExtract[1].append(c)
                        change = False
                    else:
                        currentExtract[1][-1] += c
            
            
            
            # --------------- Position ---------------
            elif onPosition:
                
                if c == "(" and not error:
                    currentExtract.append([])
                    change = False
                
                elif c == ",":
                    
                    if not change and not error:
                        
                        try:
                            currentExtract[2][-1] = int(currentExtract[2][-1])
                            change = True
                        except:
                            error = True
                            change = False
                            currentExtract[2] = Player.BASE_POSITION
                    
                    elif change:
                        change = False
                        onSize = True
                        onUsername, onColor, onPosition = False, False, False
                        change, error = False, False
                
                elif c == ")":
                    
                    if not error:
                        try:
                            currentExtract[2][-1] = int(currentExtract[2][-1])
                        except:
                            error = True
                            currentExtract[2] = Player.BASE_POSITION
                    
                    change = True
                
                elif not error:
                    if len(currentExtract[2]) == 0 or change:
                        currentExtract[2].append(c)
                        change = False
                    else:
                        currentExtract[2][-1] += c
            
            
            
            # --------------- Size ---------------
            elif onSize:
                
                if c == "(" and not error:
                    currentExtract.append([])
                    change = False
                
                elif c == ",":
                    
                    if not change and not error:
                        
                        try:
                            currentExtract[3][-1] = int(currentExtract[3][-1])
                            change = True
                        except:
                            error = True
                            change = False
                            currentExtract[3] = Player.BASE_SIZE
                
                
                elif c == ")":
                    
                    if not error and not change:
                        try:
                            currentExtract[3][-1] = int(currentExtract[3][-1])
                        except:
                            error = True
                            currentExtract[3] = Player.BASE_SIZE
                        
                        change = True
                    
                    if change:
                        onUsername, onColor, onPosition, onSize = False, False, False, False
                        change, error = False, False
                
                elif not error:
                    if len(currentExtract[3]) == 0 or change:
                        currentExtract[3].append(c)
                        change = False
                    else:
                        currentExtract[3][-1] += c
            
            
            
            else:
                
                if c == "[":
                    pass
                
                elif c == "(":
                    currentExtract = []
                    onUsername = True
                    onColor, onPosition, onSize = False, False, False
                    change, error = False, False
                
                elif c == "," or c == "]":
                    print("Players !")
                    playersList.append(Player(username=currentExtract[0],
                                              color=tuple(currentExtract[1]),
                                              position=tuple(currentExtract[2]),
                                              size=tuple(currentExtract[3])))
        
        

        return playersList
