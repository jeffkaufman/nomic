import os
import math
import random
import re
import requests
import subprocess
import time
import unidiff

def request(url):
  request_headers = {'User-Agent': 'jeffkaufman/nomic'}
  response = requests.get(url, headers=request_headers)

  for header in ['X-RateLimit-Limit',
                 'X-RateLimit-Remaining',
                 'X-RateLimit-Reset']:
    if header in response.headers:
      print('    > %s: %s' % (header, response.headers[header]))

  if response.status_code != 200:
    print('   > %s' % response.content)

  response.raise_for_status()
  return response

def get_repo():
  return os.environ['TRAVIS_REPO_SLUG']

def get_pr():
  return os.environ['TRAVIS_PULL_REQUEST']

def get_commit():
  return os.environ['TRAVIS_PULL_REQUEST_SHA']

def get_pr_diff():
  # Allow inspecting the changes this PR introduces.
  response = request('https://patch-diff.githubusercontent.com/raw/%s/pull/%s.diff' % (
      get_repo(), get_pr()))
  return unidiff.PatchSet(response.content.decode('utf-8'))

def base_pr_url():
  # This is configured in nginx like:
  #
  # proxy_cache_path
  #     /tmp/github-proxy
  #     levels=1:2
  #     keys_zone=github-proxy:1m
  #     max_size=100m;
  #
  # server {
  #   ...
  #   location /nomic-github/repos/jeffkaufman/nomic {
  #     proxy_cache github-proxy;
  #     proxy_ignore_headers Cache-Control Vary;
  #     proxy_cache_valid any 1m;
  #     proxy_pass https://api.github.com/repos/jeffkaufman/nomic;
  #     proxy_set_header
  #         Authorization
  #         "Basic [base64 of 'username:token']";
  #   }
  #
  # Where the token is a github personal access token:
  #   https://github.com/settings/tokens
  #
  # There's an API limit of 60/hr per IP by default, and 5000/hr by
  # user, and we need the higher limit.
  #
  # Responses are cached for one minute by this proxy.  The caching is
  # optional, but now that https:/www.jefftk.com/nomic is available and
  # world-accessible it could potentilly get hit by substantial traffic.  At a
  # 60s cache and 5k/hr limit we can have 83 GitHub API requests per page
  # render and not go down.  As of 2018-01-18 there are eight open PRs, each
  # of which needs a request to get reviews, so we're ok by a factor of 10.  If
  # we have a lot of old open PRs we don't care about we could either close
  # them or make the dashboard only gather reviews for PRs in the "reviewme"
  # state.
  return 'https://www.jefftk.com/nomic-github/repos/%s/pulls/%s' % (
    get_repo(), get_pr())

def get_author(pr_json):
  return pr_json['user']['login']

def get_reviews():
  target_commit = get_commit()
  print('Considering reviews at commit %s' % target_commit)

  base_url = '%s/reviews' % base_pr_url()
  url = base_url
  reviews = {}

  while True:
    response = request(url)

    for review in response.json():
      user = review['user']['login']
      commit = review['commit_id']
      state = review['state']

      print('  %s: %s at %s' % (user, state, commit))
      if state == 'APPROVED' and commit != target_commit:
        # An approval clears out any past rejections from a user.
        try:
          del reviews[user]
        except KeyError:
          pass # No past rejections for this user.

        # Only accept approvals for the most recent commit, but have rejections
        # last until overridden.
        continue

      if state == 'COMMENTED':
        continue  # Ignore comments.

      reviews[user] = state

    if 'next' in response.links:
      # This unfortunately points to GitHub, and not to the rate-limit-avoiding
      # proxy.  Pull off the query string (ex: "?page=3") and append that to
      # our url that goes via the proxy.
      next_url = response.links['next']['url']
      github_api_path, query_string = next_url.split('?')
      url = '%s?%s' % (base_url, query_string)
    else:
      return reviews

def get_users():
  return list(sorted(os.listdir('players/')))

def get_user_points():
  points = {}

  for user in get_users():
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

def iso8601_to_ts(iso8601):
  return int(time.mktime(time.strptime(iso8601, "%Y-%m-%dT%H:%M:%SZ")))

def pr_created_at_ts(pr_json):
  return iso8601_to_ts(pr_json['created_at'])

def pr_pushed_at_ts(pr_json):
  return iso8601_to_ts(pr_json['head']['repo']['pushed_at'])

def pr_last_changed_ts(pr_json):
  return max(pr_created_at_ts(pr_json),
             pr_pushed_at_ts(pr_json))

def last_commit_ts():
  # When was the last commit on master?
  cmd = ['git', 'log', 'master', '-1', '--format=%ct']
  completed_process = subprocess.run(cmd, stdout=subprocess.PIPE)
  if completed_process.returncode != 0:
    raise Exception(completed_process)

  return int(completed_process.stdout)

def seconds_since(ts):
  return int(time.time() - ts)

def seconds_to_days(seconds):
  return int(seconds / 60 / 60 / 24)

def print_points():
  print('Points:')
  for user, user_points in get_user_points().items():
    print('  %s: %s' % (user, user_points))

def days_since(ts):
  return seconds_to_days(seconds_since(ts))

def days_since_last_commit():
  return days_since(last_commit_ts())

def days_since_pr_created(pr_json):
  return days_since(pr_created_at_ts(pr_json))

def print_file_changes(diff):
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

def determine_if_mergeable():
  print_points()

  diff = get_pr_diff()
  print_file_changes(diff)

  users = get_users()
  print('Users:')
  for user in users:
    print('  %s' % user)

  pr_json = request(base_pr_url()).json()
  author = get_author(pr_json)
  print('\nAuthor: %s' % author)

  reviews = get_reviews()
  if author in users:
    reviews[author] = 'APPROVED'

  print('\nReviews:')
  for user, state in sorted(reviews.items()):
    print ('  %s: %s' % (user, state))

  approvals = []
  rejections = []
  for user in users:
    if user in reviews:
      review = reviews[user]
      if review == 'APPROVED':
        approvals.append(user)
      else:
        rejections.append(user)

  if rejections:
    raise Exception('Rejected by: %s' % (' '.join(rejections)))

  days_since_last_changed = days_since(pr_last_changed_ts(pr_json))

  print('FYI: this PR has been sitting for %s days' % (
      days_since_last_changed))

  required_approvals = math.ceil(len(users) * 2 / 3)

  # Allow three days to go by with no commits, but if longer happens then start
  # lowering the threshold for allowing a commit.
  approvals_to_skip = days_since_last_commit() - 3
  if approvals_to_skip > 0:
    print("Skipping up to %s approvals, because it's been %s days"
          " since the last commit." % (approvals_to_skip,
                                      days_since_last_commit()))
    required_approvals -= approvals_to_skip

  print('Approvals: got %s (%s) needed %s' % (
      len(approvals), ' '.join(approvals), required_approvals))

  if len(approvals) < required_approvals:
    raise Exception('Insufficient approval')

  # Don't allow PRs to be merged the day they're created unless they pass unanimously
  if (len(approvals) < len(users)) and (days_since_pr_created(pr_json) < 1):
    raise Exception('PR created within last 24 hours does not have unanimous approval.')

  print('\nPASS')

def determine_if_winner():
  print_points()

  users = get_users()
  for user in users:
    if random.random() < 0.0001:
      raise RuntimeException('%s wins!' % user)
  print('The game continues.')

def start():
  if get_pr() == 'false':
    determine_if_winner()
  else:
    determine_if_mergeable()

if __name__ == '__main__':
  start()
