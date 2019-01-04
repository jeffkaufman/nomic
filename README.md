# nomic

To join the game, make a pull request to add your github username to players.txt

Once you're playing, propose rule changes by making pull requests.

Pull requests can only be merged if validate.py, running on master,
decides they should be.  validate-on-master.sh and .travis.yml are out
of bounds.

The winner is the first player where a master build (run in response
to merging a PR) fails, saying they're the winner.
