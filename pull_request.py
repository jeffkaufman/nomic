import unidiff

import util

class PullRequest:
  def __init__(self, repo, pr_number, target_commit, users):
    self.repo_ = repo
    self.pr_number_ = pr_number
    self.target_commit_ = target_commit
    self.users_ = users

    self.pr_json_ = util.request(self.base_pr_url_()).json()

    self.reviews = self.calculate_reviews_()
    if self.author() in users:
      self.reviews[self.author()] = 'APPROVED'

    self.approvals = []
    self.rejections = []
    for user in users:
      if user in self.reviews:
        review = self.reviews[user]
        if review == 'APPROVED':
          self.approvals.append(user)
        else:
          self.rejections.append(user)

    self.non_participants = [ user for user in users
                              if user not in self.approvals
                              and user not in self.rejections ]

  def created_at_ts(self):
    return util.iso8601_to_ts(self.pr_json_['created_at'])

  def pushed_at_ts(self):
    return util.iso8601_to_ts(self.pr_json_['head']['repo']['pushed_at'])

  def last_changed_ts(self):
    return max(self.created_at_ts(),
               self.pushed_at_ts())

  def days_since_created(self):
    return util.days_since(self.created_at_ts())

  def days_since_pushed(self):
    return util.days_since(self.pushed_at_ts())

  def days_since_changed(self):
    return util.days_since(self.last_changed_ts())

  def calculate_reviews_(self):
    base_url = '%s/reviews' % self.base_pr_url_()
    url = base_url
    reviews = {}
  
    while True:
      response = util.request(url)
  
      for review in response.json():
        user = review['user']['login']
        commit = review['commit_id']
        state = review['state']
  
        if state == 'APPROVED' and commit != self.target_commit_:
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

  def base_pr_url_(self):
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
      self.repo_, self.pr_number_)

  def diff(self):
    response = util.request('https://patch-diff.githubusercontent.com/raw/%s/pull/%s.diff' % (
        self.repo_, self.pr_number_))
    return unidiff.PatchSet(response.content.decode('utf-8'))

  def author(self):
    return self.pr_json_['user']['login']



