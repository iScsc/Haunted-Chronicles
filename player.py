import common
import interpretor

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
        try :
            playersList = []
            
            string=interpretor.spc(playersString)
            string.remove('[')
            string.remove(']')
            
            for s in string:
                s='('+s+')'
                playersList.append(interpretor.interp(s,player=Player())['player'])

            return playersList
        
        except :
            return None

