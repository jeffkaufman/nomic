# nomic

## Joining

Make a pull request to add your github username a file with your github 
username like:

    players/$yourname/bonuses/initial

The file should contain the number 10.  Then ping Jeff (jeffkaufman) so you can
be added to the repo collaborators.

If Jeff doesn't add you to the list of repo collaborators, ping him to ask him
to.  This will allow you to press the merge button yourself.

## Playing

Once you're playing, propose rule changes by making pull requests.  There are
no turns, just go for it.  Vote on other people's changes by reviewing them.
Use the dashboard found at https://www.jefftk.com/nomic to track which PRs you
haven't reviewed.

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

* Pushing to branches in jeffkaufman/nomic other than master.

After your pull request has gotten all of its approvals you'll need to restart
the Travis build before the build will go green.

## Running locally

validate.py depends on some environment variables that TravisCI sets.  To run
locally you can do:

    TRAVIS_PULL_REQUEST_SHA=$(git log -1 --format='%H') \
    TRAVIS_PULL_REQUEST=<your PR number> \
    TRAVIS_REPO_SLUG=jeffkaufman/nomic \
    python3 validate.py
