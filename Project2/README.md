# Consensus Programming Project

Grant Nelson and John M. Singleton

CSCI 520 - Distributed Systems

Due Apr 6, 2020 by 11:59 PM

## Preparing the project

- You will need websockets: `pip install websockets`
- For this project we are using python 3
- Make sure the URLs for the servers are correct for local (default)
  or AWS depending on how the project is being run.

## To run client server(s)

- `cd clientServer`
- Pick a color to run (or run both):
  - For Red run `python ./main.py 0`
  - For Blue run `python ./main.py 1`
- In a browser open `http://localhost:8080/`
- Press "q", "w", "a", and "s"
- Press "r" to reset the game
- Press "ctrl+C" to kill server
  (for some reason this only works if the browser has connected to the server)

## To run Raft server(s)

- `cd raftServer`
- Startup a server with `python ./main.py <ID> <Num>`
  - where `<ID>` is the server's node ID between 0 and 4
  - and `<Num>` is the number of servers that will be run between 1 and 5
  - example `python ./main.py 0 2`
- Startup as many servers are needed for testing, odd numbers work best.
- Press enter to kill server

## Other Information

- All associated images were created by Grant Nelson
- Based off of *Rock 'Em Sock 'Em Robots* by Mattel
