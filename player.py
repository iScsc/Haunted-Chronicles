class Player:
    
    def __init__(self, ip="", username="", color=(0,0,0), position=(0,0), size=[10, 10]):
        self.ip = ip
        self.username = username
        self.color = color
        self.position = position
        self.size = size
    
    def toTuple(self):
        msg = "(" + str(self.username) + "," + str(self.color) + "," + str(self.position) + "," + str(self.size) + ")"
        return msg.replace(" ", "")
