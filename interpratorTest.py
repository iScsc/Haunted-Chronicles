from player import Player

def main():
    
    msg = "[('a',(1,1,1),(1,1),(1,1)),(b,(1,2,3),(1,2),(3,4)),(c'd',(11,12,12),(25,31),(87,32))]"
    players = Player.toPlayers(msg)
    
    for player in players:
        print(player.toString())

if __name__ == "__main__":
    main()
