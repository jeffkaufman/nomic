import util

def should_allow(pr):
  return all(user in pr.approvals for user in util.users())
