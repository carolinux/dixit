# Dixit API

The backend of a web app with that allows friends to play Dixit online. Uses a custom deck designed by carolinux. The frontend's first iteration was developed by [Eleni Mandilara](https://github.com/emandilara/dixit-web) in React and has since been extended by carolinux in her [fork](https://github.com/carolinux/dixit-web).

# Rules & game logic

- 2-6 players
- At each round, there is a *Narrator*, who chooses a card and types a phrase


# Technology

This was hacked together in a week over Christmas break in 2021 and as such is riddled with inefficiencies. However (!) it works fine for the purpose of playing over Zoom calls and lives under [dixit.lucidcode.ch](https://dixit.lucidcode.ch]) but is mostly asleep.

- Uses flask and repeated polling (every player asks about the game state every few seconds). Not scalable at the moment, however it is designed to allow multiple games to run at the same time. When I learn how to implement long polling, it will be more scalable. I don't think I'm ever going to use sockets for this.
- Also if multiple people press the NEXT ROUND button at the same time in a given game, there may be race conditions, because there are multiple threads and I don't check for concurrent access to the Mega Game State variable.
- There is no database, everything is Python objects in memory. Game logs are exported on shutdown for posterity.
