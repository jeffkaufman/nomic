import util
import pull_request
import json
import pprint

def should_allow(pr):
  # If a PR consists only of creating files in the form merged_prs/N, and the
  # files are the same as PullRequest(N).info() would generate, then allow the
  # PR in.
  #
  # The goal here is to get information about the review process for merged PRs
  # into the repo, so we can do things like give points for healthy
  # participation.
  diff = pr.diff()
  if diff.modified_files or diff.removed_files:
    raise Exception('All file changes must be additions')

  for added_file in diff.added_files:
    s_merged_prs, s_merged_pr_n = added_file.path.split('/')
    if s_merged_prs != 'merged_prs':
      raise Exception('Added file %s is not a PR info file' % added_file)

    merged_pr_n = int(s_merged_pr_n)  # will raise if not an int

    with open(added_file.path) as inf:
      tentative_pr_info = json.loads(inf.read())

    merged_pr = pull_request.PullRequest(repo=pr.get_repo(),
                                         pr_number=merged_pr_n,
                                         target_commit=None,
                                         users=util.users())
    trusted_pr_info = merged_pr.info()

    if tentative_pr_info != trusted_pr_info:
      print('\ntentative:')
      pprint.pprint(tenative_pr_info)

      print('\ntrusted:')
      pprint.pprint(trusted_pr_info)

      raise Exception('Proposed PR info does not match trusted info.')

  return True  # Only additions, and all additions are ok.
