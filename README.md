# PotatOnline
A small project to discover online multiplayer games.

## Development Plan :
- One shall be project manager
- Split development in two : client and server
- Setup Docker to host online games


## Main issues :
- Write our own protocol (App layer) ? Or simply use pinkle (object serialization) which can be easily used to hack computers ?
- More ?

## Milestones :
- LAN 'mail' service using python ? (one way first and then both) ***<font color="green">DONE !</font>***
- Based on this service, use it to make an object move on the other computer's screen. ***DONE !***
- Make a game playable in LAN. ***WIP !***
- Make it playable online through the iscsc server.


## GAME :

### Formatted messages :

#### Client sends :
- `CONNECT <Username> END` and receives `CONNECTED <Username> <Screen_Size> STATE <Players_List> END` as a connection confirmation and to setup the state of the game locally.
- `INPUT <Username> <Input> END` and receives `STATE <Players_List> END` to update the state of the game on the server, and then locally. `<Input>` can be `L`, `R`, `U`, `D` for movements, and `.` for none.
- `DISCONNECT <Username> END` and receives `DISCONNECTED <Username> END` as a confirmation before quitting the game.
