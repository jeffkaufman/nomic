import os
import requests
import subprocess

def request(url):
  request_headers = {'User-Agent': 'jeffkaufman/nomic'}
  response = requests.get(url, headers=request_headers)
  response.raise_for_status()
  return response

def base_pr_url():
  return 'https://api.github.com/repos/%s/pulls/%s' % (
    os.environ['TRAVIS_REPO_SLUG'],
    os.environ['TRAVIS_PULL_REQUEST'])

def get_author():
  response = request(base_pr_url())
  return response.json()['user']['login']

def get_reviews():
  url = '%s/reviews' % base_pr_url()
  reviews = {}

  while True:
    response = request(url)

    for review in response.json():
      user = review['user']['login']
      state = review['state']
      if state == 'COMMENTED':
        continue
      reviews[user] = state

    if 'next' in response.links:
      url = response.links['next']['url']
    else:
      return reviews

def get_users():
  cmd = ['git', 'show', 'master:players.txt']
  print('Running command "%s"' % ' '.join(cmd))
  process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  (output, err) = process.communicate()
  exit_code = process.wait()

  print('Output: %s' % output)
  if err:
    print('Error: %s' % err)

  if exit_code != 0:
    raise Exception('Failed with exit code %s.' % exit_code)

  users = set()
  for line in output.decode("utf-8").split('\n'):
    line = line.strip()
    if line:
      users.add(line.strip())

  return list(sorted(users))

def start():
  users = get_users()
  print('Users:')
  for user in users:
    print('  %s' % user)

  author = get_author()
  print('\nAuthor: %s' % author)

  reviews = get_reviews()
  reviews[author] = 'APPROVED'

  print('\nReviews:')
  for user, state in sorted(reviews.items()):
    print ('  %s: %s' % (user, state))

  approval_count = 0
  for user in users:
    if reviews.get(user, None) == 'APPROVED':
      approval_count += 1

  if approval_count < len(users):
    raise Exception('Insufficient approval.')

  print('\nPASS')

if __name__ == '__main__':
  start()
