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
