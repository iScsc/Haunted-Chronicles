class Wall:
    
    BASE_COLOR = (255, 0, 0)
    BASE_POSITION = (0, 0)
    BASE_SIZE = (50, 50)
    
    def __init__(self, id=0, color=(0,0,0), position=(0,0), size=[10, 10]):
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
    
    
    def toString(self):
        """Generate the string representation of the wall.

        Returns:
            str: description of the wall used to send data from the server to the clients.
        """
        msg = "(" + str(self.color) + "," + str(self.position) + "," + str(self.size) + ")"
        return msg.replace(" ", "")