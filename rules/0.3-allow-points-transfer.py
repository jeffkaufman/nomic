import util


def should_allow(pr):
    # If a PR only moves points around by the creation of new bonus files, has
    # been approved by every player losing points, reduces the total number of
    # points, and does not create any new users, allow it.
    #
    # Returns to indicate yes, raises an exception to indicate no.
    #
    # Having a PR merged gives you a point (#33), so a PR like:
    #
    #  - me:  -2 points
    #  - you: +1 point
    #
    # is effectively:
    #
    #  - me:  -1 point
    #  - you: +1 point

    bonuses = pr.get_new_bonuses_or_raise()

    total_points_change = 0
    for points_user, points_name, points_change in bonuses:
        if points_user not in util.users():
            raise Exception('Points transfer PRs should not add users: got %s' %
                            points_user)

        if points_change < 0:
            if points_user not in pr.approvals:
                raise Exception('Taking %s points from %s requires their approval.' % (
                    abs(points_change), points_user))

        total_points_change += points_change

    if total_points_change >= 0:
        raise Exception('points change PRs must on net remove points')

    return True
