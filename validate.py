import os
import random
import requests

def request(url):
  request_headers = {'User-Agent': 'jeffkaufman/nomic'}
  response = requests.get(url, headers=request_headers)

  for header in ['X-RateLimit-Limit',
                 'X-RateLimit-Remaining',
                 'X-RateLimit-Reset']:
    if header in response.headers:
      print('    > %s: %s' % (header, response.headers[header]))

  response.raise_for_status()
  return response

def get_repo():
  return os.environ['TRAVIS_REPO_SLUG']

def get_pr():
  return os.environ['TRAVIS_PULL_REQUEST']

def base_pr_url():
  return 'https://api.github.com/repos/%s/pulls/%s' % (
    get_repo(), get_pr())

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
  users = set()
  with open('players.txt') as inf:
    for line in inf:
      line = line.strip()
      if line:
        users.add(line.strip())
  return list(sorted(users))

def determine_if_mergeable():
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
