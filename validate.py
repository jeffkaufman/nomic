import os
import requests

def request(url):
  request_headers = {'User-Agent': 'jeffkaufman/nomic'}
  response = requests.get(url, headers=request_headers)
  response.raise_for_status()
  return response.json()

def base_pr_url():
  return 'https://api.github.com/repos/%s/pulls/%s' % (
    os.environ['TRAVIS_REPO_SLUG'],
    os.environ['TRAVIS_PULL_REQUEST'])

def get_author():
  response = request(base_pr_url())
  return response['user']

def get_reviews():
  url = '%s/reviews' % base_pr_url()
  reviews = {}

  while True:
    response = request(url)

    for review in response:
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
      users.add(line.strip())
  return list(sorted(users))

def start():
  author = get_author()
  print ("Author: %s" % author)

  reviews = get_reviews()
  reviews[author] = 'APPROVED'

  print ('Reviews:')
  for user, state in sorted(reviews.items()):
    print ('  %s: %s' % (user, state))

  users = get_users()
  approval_count = 0
  for user in users:
    if reviews.get(user, None) == 'APPROVED':
      approval_count += 1

  unanimous = (approval_count == len(users))
  majority = (approval_count / len(users) > 0.5)

  if unanimous:
    print ('Unanimous')
  elif majority:
    print ('Majority')
  else:
    print ('Failed')

if __name__ == '__main__':
  start()
