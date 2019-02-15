import os
import util

# This value set to 0 until we figure out a good way to prevent dummy account abuse
max_start_bonus = 0

def should_allow(pr):
  bonuses = pr.get_new_bonuses_or_raise()
  
  if len(bonuses) > 1:
    raise Exception('Only one new player can be added in a PR')
  elif len(bonuses) < 1:
    raise Exception('Empty diff?')
  
  (points_user, points_name, points_change) = bonuses[0]
  
  if pr.author != points_user:
    raise Exception('New players should submit their own PRs, but %s submitted the PR to add %s' %
                    (pr.author, points_user))
  
  if points_name != 'initial':
    raise Exception('New player bonus value is called %s instead of "initial"' % points_name)
    
  if points_change < 0:
    raise Exception('Points cannot be negative')

  if points_change > max_start_bonus:
    raise Exception('%s initial points exceeds maximum starting value of %s points' %
                    (points_change, max_start_bonus))
  
  bonus_directory = os.path.join('players', points_user, 'bonuses')
  if os.path.isdir(bonus_directory):
    for bonus in os.listdir(bonus_directory):
      if bonus != 'initial':
        raise Exception('%s already has bonuses' % points_user)

  return True
