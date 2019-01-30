import os
import re
import requests
import subprocess
import time

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

def iso8601_to_ts(iso8601):
  return int(time.mktime(time.strptime(iso8601, "%Y-%m-%dT%H:%M:%SZ")))

def users():
  return list(sorted(os.listdir('players/')))

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

def days_since(ts):
  return seconds_to_days(seconds_since(ts))

def days_since_last_commit():
  return days_since(last_commit_ts())

def get_user_points():
  points = {}

  for user in users():
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

