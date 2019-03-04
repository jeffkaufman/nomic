import util


def should_block(pr):
    # Don't allow PRs to be merged the day they're created unless they pass unanimously
    if len(pr.approvals) < len(util.users()) and (pr.days_since_created() < 1):
        raise Exception('PR created within last 24 hours does not have unanimous approval.')
