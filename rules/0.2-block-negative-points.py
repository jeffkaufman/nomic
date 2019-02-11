import util

def should_block(pr):
  for user, user_points in util.get_user_points().items():
    if util.total_user_points(user_points) < 0:
      raise Exception('Would bring user %s points to %s which is negative.' %
                      (user, user_points))
