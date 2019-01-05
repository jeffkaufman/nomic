# nomic

To join the game, make a pull request to add your github username to players.txt.
Then ping Jeff so you can be added to the repo collaborators.

Once you're playing, propose rule changes by making pull requests.

Pull requests can only be merged if validate.py, running on master,
decides they should be.  validate-on-master.sh and .travis.yml are out
of bounds.

After your pull request has gotten all of its approvals you'll need to restart
the Travis build before the build will go green.

The winner is the first player where a master build (run in response
to merging a PR) fails, saying they're the winner.
