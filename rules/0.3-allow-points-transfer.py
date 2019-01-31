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

  diff = pr.diff()
  if diff.modified_files or diff.removed_files:
    raise Exception('All file changes must be additions')

  total_points_change = 0

  for added_file in diff.added_files:
    s_players, points_user, s_bonuses, bonus_name =  added_file.path.split('/')
    if s_players != 'players' or s_bonuses != 'bonuses':
      raise Exception('Added file %s is not a bonus file' % added_file)

    if points_user not in util.users():
      raise Exception('Points transfer PRs should not add users: got %s' %
                      points_user)

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

  return True
