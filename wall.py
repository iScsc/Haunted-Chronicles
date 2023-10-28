class Wall:
    
    BASE_COLOR = (255, 0, 0)
    BASE_POSITION = (0, 0)
    BASE_SIZE = (50, 50)
    
    def __init__(self, id=0, color=BASE_COLOR, position=BASE_POSITION, size=BASE_SIZE):
        """Create a new wall with given parameters.

        Args:
            - id (int): id
            - color (tuple): Color used by the wall.
            - position (tuple): Position of the wall.
            - size (list): Size of the wall.
        """
        
        self.id = id
        self.color = color
        self.position = position
        self.size = size
    
    
    
    def toList(self):
        """Generate the list representation of the wall with the format [id, color, position, size]

        Returns:
            list: extraction of the wall's attributes.
        """
        return self.id, self.color, self.position, self.size
    
    
    
    def toString(self):
        """Generate the string representation of the wall.

        Returns:
            str: description of the wall used to send data from the server to the clients.
        """
        msg = "(" + str(id) + "," + str(self.color) + "," + str(self.position) + "," + str(self.size) + ")"
        return msg.replace(" ", "")
    
    
    
    def toWalls(wallsString):
        """Generate the list of walls described by the wallsString variable.

        Args:
            wallsString (str): string representation of the list of walls.
            It shall be of the format : "[wall1, wall2, wall3, ...]
            where a wall is : (id, (color.r, color.g, color.b), (position.x, position.y), (width, height))

        Returns:
            list[Wall]: list of walls to display on the client side.
        """
        
        wallsList = []
        
        currentExtract = None
        c=''
        
        onId, onColor, onPosition, onSize = False, False, False, False
        change = False # spot changes of fields in multiple fields variables like tuples
        error = False # spot errors in fields
        
        for i in range(len(wallsString)):
            # #? Debug prints :
            # print("------------------------------------")
            # print("Current char = ", c)
            # print("currentExtract = ", currentExtract)
            # print("wallsList = ", wallsList)
            # print("change = ", change, " | error = ", error)
            # print("onId = ", onId, " | onColor = ", onColor, " | onPosition = ", onPosition, " | OnSize = ", onSize)
            
            c = wallsString[i]
            
            
            try:
                # --------------- Error ----------------
                if error : 
                    return None
                
                # --------------- Username ---------------
                elif onId:
                    
                    if c != ",":

                        if len(currentExtract) == 0:
                            currentExtract.append(c)
                        else:
                            currentExtract[0] += c
                    
                    else:
                        currentExtract[0] = int(currentExtract[0])
                        onColor = True
                        onId, onPosition, onSize = False, False, False
                        change = False
                
                
                
                # --------------- Color ---------------
                elif onColor:
                    
                    if c == "(" :
                        currentExtract.append([])
                        change = False
                    
                    elif c == ",":
                        
                        if not change :
                            currentExtract[1][-1] = int(currentExtract[1][-1])
                            change = True
                        
                        elif change:
                            change = False
                            onPosition = True
                            onId, onColor, onSize = False, False, False
                            change = False
                    
                    elif c == ")":
                        currentExtract[1][-1] = int(currentExtract[1][-1])
                        change = True
                        
                    
                    else:
                        if len(currentExtract[1]) == 0 or change:
                            currentExtract[1].append(c)
                            change = False
                        else:
                            currentExtract[1][-1] += c
                
                
                
                # --------------- Position ---------------
                elif onPosition:
                    
                    if c == "(" :
                        currentExtract.append([])
                        change = False
                    
                    elif c == ",":
                        
                        if not change :
                            currentExtract[2][-1] = float(currentExtract[2][-1])
                            change = True
                        
                        elif change:
                            change = False
                            onSize = True
                            onId, onColor, onPosition = False, False, False
                            change = False
                    
                    elif c == ")":
                        currentExtract[2][-1] = float(currentExtract[2][-1])
                        change = True
                    
                    else:
                        if len(currentExtract[2]) == 0 or change:
                            currentExtract[2].append(c)
                            change = False
                        else:
                            currentExtract[2][-1] += c
                
                
                
                # --------------- Size ---------------
                elif onSize:
                    
                    if c == "(" :
                        currentExtract.append([])
                        change = False
                    
                    elif c == ",":
                        
                        if not change :
                            currentExtract[3][-1] = float(currentExtract[3][-1])
                            change = True
                    
                    elif c == ")":
                        
                        if not change:
                            currentExtract[3][-1] = float(currentExtract[3][-1])
                            change = True
                        
                        else:
                            onId, onColor, onPosition, onSize = False, False, False, False
                            change = False
                    
                    else:
                        if len(currentExtract[3]) == 0 or change:
                            currentExtract[3].append(c)
                            change = False
                        else:
                            currentExtract[3][-1] += c
                            
                            
                            
                # --------------- Create new player ---------------
                else:
                    
                    if c == "[":
                        pass
                    
                    elif c == "(":
                        currentExtract = []
                        onId = True
                        onColor, onPosition, onSize = False, False, False
                        change = False
                    
                    elif c == "," or c == "]":
                        wallsList.append(Wall(id=currentExtract[0],
                                                color=tuple(currentExtract[1]),
                                                position=tuple(currentExtract[2]),
                                                size=tuple(currentExtract[3])))
                        
                        
            except: # if any error occured
                error=True
                
        

        return wallsList
