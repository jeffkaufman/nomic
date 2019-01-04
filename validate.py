import os
import requests

def base_pr_url():
  return 'https://api.github.com/repos/%s/pulls/%s' % (
    os.environ['TRAVIS_REPO_SLUG'],
    os.environ['TRAVIS_PULL_REQUEST'])

def get_reviews():
  url = '%s/reviews' % base_pr_url()
  user_states = {}

  while True:
    request_headers = {'User-Agent': 'jeffkaufman/nomic'}
    response = requests.get(url, headers=request_headers)
    response.raise_for_status()

    for review in response.json():
      user = review['user']['login']
      state = review['state']
      if state == 'COMMENTED':
        continue
      user_states[user] = state

    if 'next' in response.links:
      url = response.links['next']['url']
    else:
      return user_states

def get_users():
  users = set()
  with open('players.txt') as inf:
    for line in inf:
      users.add(line.strip())
  return list(sorted(users))      

def start():
  reviews = get_reviews()
  if not reviews:
    raise Exception('no reviews')
  
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
