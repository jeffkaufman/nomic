# nomic

## Joining

Make a pull request to add your github username a file with your github 
username like:

    players/$yourname/bonuses/initial

This file should contain your initial number of points.  If you choose to
start with 0 points, your pull request won't require approval from existing
players.  You can also choose to start with more points, but you'll need to
wait for other players to approve your PR.  Either way, ping Jeff
(jeffkaufman) so you can be added to the repo collaborators.  This will allow
you to press the merge button yourself.

## Playing

Once you're playing, propose rule changes by making pull requests.  There are
no turns, just go for it.  Vote on other people's changes by reviewing them.
Use the dashboard found at https://www.jefftk.com/nomic to track which PRs you
haven't reviewed.

You're expected to check in daily to see if there's anything that needs your
review.  If something looks hard to review, comment saying so instead of just
silently putting off your review.

When you have a PR ready for review, add the label 'reviewme' on it so people
know it needs review.  Otherwise it won't show up on the dashboard.

## Winning

The winner is the first player where a master build (run in response
to merging a PR) fails saying they're the winner.

## Mechanics

Pull requests can only be merged if validate.py, running on master,
decides they should be.  Some things are out of bounds:

* validate-on-master.sh, .travis.yml, requirements.txt and anything else that
  begins executing before validate.py has gotten a chance to begin running on
  master.

* Editing the text of a merge commit when merging the PR.

* Pushing from the command line to any branches in jeffkaufman/nomic.  To merge
  to master use the big green button.

After your pull request has gotten all of its approvals you'll need to restart
the Travis build before the build will go green.

## Running locally

`./run.sh` Simulate Travis in determining whether someone has won.

`./run.sh <PR>` Simulate Travis in determing whether a PR can merge.

PRs can't be merged unless they pass type checks, and type checks don't run on
Travis until all checks on Master pass, which they won't until your PR is
approved.  So run locally to verify types are ok and you won't be surprised
when a PR you thought was ready can't actually go in.

