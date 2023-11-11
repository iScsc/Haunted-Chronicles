import common
import interpretor

class Wall:
    
    BASE_COLOR = common.Color()
    BASE_POSITION = common.Position()
    BASE_SIZE = common.Size()
    
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
    
    
    
    def __str__(self):
        """Generate the string representation of the wall.

        Returns:
            str: description of the wall used to send data from the server to the clients.
        """
        msg = "(" + str(self.id) + "," + str(self.color) + "," + str(self.position) + "," + str(self.size) + ")"
        return msg.replace(" ", "")
    
    
    
    def toWalls(wallsString, DEBUG=False):
        """Generate the list of walls described by the wallsString variable.

        Args:
            wallsString (str): string representation of the list of walls.
            It shall be of the format : "[wall1, wall2, wall3, ...]
            where a wall is : (id, (color.r, color.g, color.b), (position.x, position.y), (width, height))

        Returns:
            list[Wall]: list of walls to display on the client side.
        """
        
        try :
            wallsList = []
            
            string=interpretor.spc(wallsString)
            string.remove("['")
            string.remove("']")
            
            for s in string:
                s='('+s+')'
                wallsList.append(interpretor.interp(s,wall=Wall())['wall'])

            return wallsList
        
        except Exception as e:
            if DEBUG:
                print(e)
            return None
