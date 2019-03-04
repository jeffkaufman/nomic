import util


def should_allow(pr):
    if not all(user in pr.approvals for user in util.users()):
        raise Exception('PR does not have unanimous approval')
    return True
