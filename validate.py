import os
import math
import random
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
  #   location /nomic-github/repos/jeffkaufman/nomic {
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
  return 'https://www.jefftk.com/nomic-github/repos/%s/pulls/%s' % (
    get_repo(), get_pr())

def get_author():
  response = request(base_pr_url())
  return response.json()['user']['login']

def get_reviews():
  target_commit = get_commit()
  print('Considering reviews at commit %s' % target_commit)

  url = '%s/reviews' % base_pr_url()
  reviews = {}

  while True:
    response = request(url)

    for review in response.json():
      user = review['user']['login']
      commit = review['commit_id']
      state = review['state']

      print('  %s: %s at %s' % (user, state, commit))
      if state == 'APPROVED' and commit != target_commit:
        # Only accept approvals for the most recent commit, but have rejections
        # last until overridden.
        continue

      if state == 'COMMENTED':
        continue  # Ignore comments.

      reviews[user] = state

    if 'next' in response.links:
      url = response.links['next']['url']
    else:
      return reviews

def get_users():
  return list(sorted(os.listdir('players/')))

def last_commit_ts():
  # When was the last commit on master?
  cmd = ['git', 'log', 'master', '-1', '--format=%ct']
  completed_process = subprocess.run(cmd, stdout=subprocess.PIPE)
  if completed_process.returncode != 0:
    raise Exception(completed_process)

  return int(completed_process.stdout)

def seconds_since_last_commit():
  return int(time.time() - last_commit_ts())

def days_since_last_commit():
  return int(seconds_since_last_commit() / 60 / 60 / 24)

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
  diff = get_pr_diff()
  print_file_changes(diff)

  users = get_users()
  print('Users:')
  for user in users:
    print('  %s' % user)

  author = get_author()
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

  print('\nPASS')

def determine_if_winner():
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
