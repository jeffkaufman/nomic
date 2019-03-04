import math
import util


def should_block(pr):
    required_approvals = math.ceil(len(util.users()) * 2 / 3)

    # Allow three days to go by with no commits, but if longer happens then start
    # lowering the threshold for allowing a commit.
    approvals_to_skip = util.days_since_last_commit() - 3
    if approvals_to_skip > 0:
        print("Skipping up to %s approvals, because it's been %s days"
              " since the last commit." % (approvals_to_skip,
                                           util.days_since_last_commit()))
        required_approvals -= approvals_to_skip

    if len(pr.approvals) < required_approvals:
        raise Exception('Insufficient approval: got %s out of %s required approvals'
                        % (len(pr.approvals), required_approvals))
