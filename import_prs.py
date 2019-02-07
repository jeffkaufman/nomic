import os
import sys
import json

import pull_request
import util

# Usage:
#   python import_prs.py <pr_number> <pr_number>
#
# Creates files that the allow-merged-pr-import rule will accept.

def start(repo_slug, *pr_numbers):
  for pr_number in pr_numbers:
    fname = os.path.join('merged_prs', pr_number)
    if os.path.exists(fname):
      raise Exception('PR %s already on file as %s' % (pr_number, fname))

    pr = pull_request.PullRequest(repo=repo_slug,
                                  pr_number=pr_number,
                                  target_commit=None,
                                  users=util.users())

    with open(fname, 'w') as outf:
      outf.write(json.dumps(pr.info()))

if __name__ == '__main__':
  repo_slug = 'jeffkaufman/nomic'
  start(repo_slug, *sys.argv[1:])
