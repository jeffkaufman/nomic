import os
import runpy
import copy
import traceback
import util
import pull_request


def print_points():
    print('Points:')
    for user, user_points in util.get_user_points().items():
        print('  %s: %s' % (user, util.total_user_points(user_points)))
        for reason in user_points:
            print('    %s: %s' % (reason, user_points[reason]))


def print_users():
    users = util.users()
    print('Users:')
    for user in users:
        print('  %s' % user)


def print_file_changes(pr):
    diff = pr.diff()
    print('\n')
    for category, category_list in [('added', diff.added_files),
                                    ('modified', diff.modified_files),
                                    ('removed', diff.removed_files)]:

        if category_list:
            print('%s:' % category)
            for patched_file in category_list:
                print('  %s' % patched_file.path)
    print()


def print_status(pr):
    print('\nAuthor: %s' % pr.author())

    print('\nReviews:')
    for user, state in sorted(pr.reviews.items()):
        print('  %s: %s' % (user, state))

    print('Approvals: %s - %s' % (len(pr.approvals), ' '.join(pr.approvals)))
    print('Rejections: %s - %s' % (len(pr.rejections), ' '.join(pr.rejections)))
    print('Non-participants: %s - %s' % (len(pr.non_participants), ' '.join(pr.non_participants)))

    print('\nFYI: this PR has been sitting for %s days' % (
        pr.days_since_changed()))

    print_file_changes(pr)


def determine_if_mergeable(pr):
    print_points()
    print_status(pr)

    rules = []
    for rule_fname in os.listdir('rules'):
        rule_priority_str, allow_block, rule_name = rule_fname.split('-', 2)
        rule_name, _ = rule_name.rsplit('.', 1)
        if allow_block not in ['allow', 'block']:
            raise Exception('Invalid rule prefix %s in %s' % (
                allow_block, rule_fname))
        is_allow = allow_block == 'allow'

        rules.append((float(rule_priority_str),
                      os.path.join('rules', rule_fname),
                      rule_name,
                      is_allow))

    # Go through rules sorted by priority, with ties broken by the filename.
    for rule_priority, rule_full_fname, rule_name, is_allow in sorted(rules):
        print('\nRunning rule %s' % rule_full_fname)

        pr_copy = copy.deepcopy(pr)

        rule_py = runpy.run_path(rule_full_fname)
        fn = rule_py['should_allow' if is_allow else 'should_block']

        if is_allow:
            try:
                # Returns truthy to indicate allowing, anything else including raising
                # for no judgement.
                if fn(pr_copy):
                    print('\nPASS: %s' % rule_name)
                    return
            except Exception as e:
                traceback.print_exc()
                print('  %s: %s' % (rule_full_fname, e))
        else:
            # Raises an exception to indicate blocking, anything else for no
            # judgement.
            fn(pr_copy)

    print('\nPASS')


def determine_if_winner():
    print_points()

    # Pick a winner at random with a single random number.  We divide the number
    # line up like:
    #
    #   [ a_points | b_points | c_points | ... everything else ... ]
    #
    # and then we choose a place on the number line randomly:
    #
    #   [ a_points | b_points | c_points | ... everything else ... ]
    #                          ^
    # or:
    #
    #   [ a_points | b_points | c_points | ... everything else ... ]
    #                                       ^
    # You can think of this as assigning a range to each player:
    #
    #   A wins if random is [0, a_points)
    #   B wins if random is [a_points, a_points + b_points)
    #   C wins if random is [a_points + b_points, a_points + b_points + c_points)
    #   no one wins if random is [a_points + b_points + c_points, 1)
    #
    # The number line defaults to a range of 100000.
    # In order to ensure fairness with large numbers of points,
    # we extend the line if total points across all players exceed that value.
    # Relative chance per-player is still preserved.

    rnd = util.random()
    all_user_points = util.get_user_points()

    summed_user_points = [(user, util.total_user_points(user_points))
                          for user, user_points in all_user_points.items()]

    # Don't include negative values when summing user points,
    # since they have no chance to win anyway
    # There shouldn't be negative values, but just in case...
    total_points = sum([user_points for user, user_points
                        in summed_user_points if user_points > 0])

    scalar = min(0.00001, 1.0 / total_points)
    points_so_far = 0

    print('Probability of winning:')
    for user, user_points in summed_user_points:
        print('%s: %.3f%%' % (user, user_points * scalar * 100))

    for user, user_points in summed_user_points:
        if rnd < scalar * (user_points + points_so_far):
            raise Exception('%s wins!' % user)
        points_so_far += user_points

    print('The game continues.')


def start():
    travis_pull_request = os.environ['TRAVIS_PULL_REQUEST']

    if travis_pull_request == 'false':
        determine_if_winner()
    else:
        target_commit = os.environ['TRAVIS_PULL_REQUEST_SHA']
        repo_slug = os.environ['TRAVIS_REPO_SLUG']
        determine_if_mergeable(pull_request.PullRequest(
            repo=repo_slug,
            pr_number=travis_pull_request,
            target_commit=target_commit,
            users=util.users()))


if __name__ == '__main__':
    start()
