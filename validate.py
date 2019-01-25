import os
import math
import random
import re
import subprocess

import util
import pull_request

def get_user_points():
  points = {}

  for user in util.users():
    points[user] = 0

    bonus_directory = os.path.join('players', user, 'bonuses')
    if os.path.isdir(bonus_directory):
      for named_bonus in os.listdir(bonus_directory):
        with open(os.path.join(bonus_directory, named_bonus)) as inf:
          points[user] += int(inf.read())

  cmd = ['git', 'log', 'master', '--first-parent', '--format=%s']
  completed_process = subprocess.run(cmd, stdout=subprocess.PIPE)
  if completed_process.returncode != 0:
    raise Exception(completed_process)
  process_output = completed_process.stdout.decode('utf-8')

  merge_regexp = '^Merge pull request #([\\d]*) from ([^/]*)/'
  for commit_subject in process_output.split('\n'):
    # Iterate through all commits in reverse chronological order.

    match = re.match(merge_regexp, commit_subject)
    if match:
      # Regexp match means this is a merge commit.

      pr_number, commit_username = match.groups()

      if int(pr_number) == 33:
        # Only look at PRs merged after this one.
        break

      if commit_username in points:
        points[commit_username] += 1

  return points

def print_points():
  print('Points:')
  for user, user_points in get_user_points().items():
    print('  %s: %s' % (user, user_points))

def print_users():
  users = util.users()
  print('Users:')
  for user in users:
    print('  %s' % user)

def print_file_changes(pr):
  diff = pr.diff()
  print('\n')
  for category, category_list in [
    ('added', diff.added_files),
    ('modified', diff.modified_files),
    ('removed', diff.removed_files)]:

    if category_list:
      print('%s:' % category)
      for patched_file in category_list:
        print('  %s' % patched_file.path)
        print()

def mergeable_as_points_transfer(pr):
  # If a PR only moves points around by the creation of new bonus files, has
  # been approved by every player losing points, reduces the total number of
  # points, allow it.
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

  print('\nConsidering whether this can be merged as a points transfer:')

  diff = pr.diff()
  if diff.modified_files or diff.removed_files:
    raise Exception('All file changes must be additions')

  total_points_change = 0

  for added_file in diff.added_files:
    s_players, points_user, s_bonuses, bonus_name =  added_file.path.split('/')
    if s_players != 'players' or s_bonuses != 'bonuses':
      raise Exception('Added file %s is not a bonus file')

    (diff_invocation_line, file_mode_line, _, removed_file_line,
     added_file_line, patch_location_line, file_delta_line,
     empty_line) = str(added_file).split('\n')

    if diff_invocation_line != 'diff --git a/%s b/%s' % (
        added_file.path, added_file.path):
      raise Exception('Unexpected diff invocation: %s' % diff_invocation_line)

    if file_mode_line != 'new file mode 100644':
      raise Exception('File added with incorrect mode: %s' % file_mode_line)

    if removed_file_line != '--- /dev/null':
      raise Exception(
        'Diff format makes no sense: added files should say they are from /dev/null')

    if added_file_line != '+++ b/%s' % added_file.path:
      raise Exception('Something wrong with file adding line: file is '
                      '%s but got %s' % (added_file.path, added_file_line))

    if patch_location_line != '@@ -0,0 +1,1 @@':
      raise Exception('Patch location makes no sense: %s' %
                      patch_location_line)

    if empty_line:
      raise Exception('Last line should be empty')

    if file_delta_line.startswith('+'):
      actual_file_delta = file_delta_line[1:]
    else:
      raise Exception('File delta missing initial + for addition: %s' %
                      file_delta_line)

    # If this isn't an int, then it raises and the PR isn't mergeable
    points_change = int(actual_file_delta)

    if points_change < 0:
      if points_user not in pr.approvals:
        raise Exception('Taking %s points from %s requires their approval.' % (
            abs(points_change), points_user))

    total_points_change += points_change

  if total_points_change >= 0:
    raise Exception('points change PRs must on net remove points')

  # Returning without an exception is how we indicate success.
  print('  yes')

def print_status(pr):
  print('\nAuthor: %s' % pr.author())

  print('\nReviews:')
  for user, state in sorted(pr.reviews.items()):
    print ('  %s: %s' % (user, state))

  print('Approvals: %s - %s' % (len(pr.approvals), ' '.join(pr.approvals)))
  print('Rejections: %s - %s' %(len(pr.rejections), ' '.join(pr.rejections)))
  print('Non-participants: %s - %s' %(len(pr.non_participants), ' '.join(pr.non_participants)))

  print_file_changes(pr)

def determine_if_mergeable(pr):
  print_points()
  print_status(pr)

  try:
    mergeable_as_points_transfer(pr)
  except Exception as e:
    print("Doesn't meet requirements for points transfer: %s" % e)
  else:
    print('Meets requirements for points transfer.  PASS')
    return

  if pr.rejections:
    raise Exception('Rejected by: %s' % (' '.join(pr.rejections)))

  print('FYI: this PR has been sitting for %s days' % (
      pr.days_since_changed()))

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
    raise Exception('Insufficient approval: got %s out of %s required approvals' % (len(pr.approvals), required_approvals))

  # Don't allow PRs to be merged the day they're created unless they pass unanimously
  if (len(pr.approvals) < len(util.users())) and (pr.days_since_created() < 1):
    raise Exception('PR created within last 24 hours does not have unanimous approval.')

  print('\nPASS')

def determine_if_winner():
  print_points()

  for user, user_points in get_user_points().items():
    if random.random() < 0.00001 * user_points:
      raise Exception('%s wins!' % user)
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
