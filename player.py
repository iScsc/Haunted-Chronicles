import common

class Player:
    
    BASE_COLOR = common.Color()
    BASE_POSITION = common.Position()
    BASE_SIZE = common.Size()
    
    def __init__(self, ip="", username="", color=BASE_COLOR, position=BASE_POSITION, size=BASE_SIZE):
        """Create a new player with given parameters.

        Args:
            - ip (str, optional): Ip address of the player (only defined on the server side).
            - username (str): Username of the player.
            - color (tuple): Color used by the player.
            - position (tuple): Position of the player.
            - size (list): Size of the player.
        """
        
        self.ip = ip
        self.username = username
        self.color = color
        self.position = position
        self.size = size
    
    
    
    def update(self, color=None, position=None, size=None):
        """Updates the player with the given parameters. If a parameter is not given, it will keep the old value.

        Args:
            - color (tuple): Color used by the player.
            - position (tuple): Position of the player.
            - size (list): Size of the player.
        """
        if color != None:
            self.color = color
        if position != None:
            self.position = position
        if size != None:
            self.size = size
    
    
    
    def toList(self):
        """Generate the list representation of the player with the format [ip, username, color, position, size]

        Returns:
            list: extraction of the player's attributes.
        """
        return self.ip, self.username, self.color, self.position, self.size
    
    
    
    def toString(self):
        """Generate the string representation of the player.

        Returns:
            str: description of the player used to send data from the server to the clients.
        """
        msg = "(" + str(self.username) + "," + str(self.color) + "," + str(self.position) + "," + str(self.size) + ")"
        return msg.replace(" ", "")



    def toPlayers(playersString):
        """Generate the list of players described by the playersString variable.

        Args:
            playersString (str): string representation of the list of players.
            It shall be of the format : "[player1, player2, player3, ...]
            where a player is : (username, (color.r, color.g, color.b), (position.x, position.y), (width, height))

        Returns:
            list[Player]: list of players to display on the client side.
        """
        
        playersList = []
        
        currentExtract = None
        
        onUsername, onColor, onPosition, onSize = False, False, False, False
        change = False # spot changes of fields in multiple fields variables like tuples
        error = False # spot errors in fields
        
        for i in range(len(playersString)):
            # #? Debug prints :
            # print("------------------------------------")
            # print("Current char = ", c)
            # print("currentExtract = ", currentExtract)
            # print("playersList = ", playersList)
            # print("change = ", change, " | error = ", error)
            # print("onUsername = ", onUsername, " | onColor = ", onColor, " | onPosition = ", onPosition, " | OnSize = ", onSize)
            
            c = playersString[i]
            
            # --------------- Username ---------------
            if onUsername:
                
                if c != ",":

                    if len(currentExtract) == 0:
                        if (c == "'" or c == '"'):
                            currentExtract.append("") # beginning of the username
                        else:
                            currentExtract.append(c)
                    elif (c == "'" or c == '"') and playersString[i + 1] == ",":
                        pass # end of the username
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
                            currentExtract[2][-1] = float(currentExtract[2][-1])
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
                            currentExtract[2][-1] = float(currentExtract[2][-1])
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
                            currentExtract[3][-1] = float(currentExtract[3][-1])
                            change = True
                        except:
                            error = True
                            change = False
                            currentExtract[3] = Player.BASE_SIZE
                
                
                elif c == ")":
                    
                    if not error and not change:
                        try:
                            currentExtract[3][-1] = float(currentExtract[3][-1])
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
            
            
            
            # --------------- Create new player ---------------
            else:
                
                if c == "[":
                    pass
                
                elif c == "(":
                    currentExtract = []
                    onUsername = True
                    onColor, onPosition, onSize = False, False, False
                    change, error = False, False
                
                elif c == "," or c == "]":
                    playersList.append(Player(username=currentExtract[0],
                                              color=tuple(currentExtract[1]),
                                              position=tuple(currentExtract[2]),
                                              size=tuple(currentExtract[3])))
        
        

        return playersList

