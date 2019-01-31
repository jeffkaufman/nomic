from typing import Dict, List
import unidiff

import util

class PullRequest:
  def __init__(self, repo: str, pr_number: str, target_commit: str, users: List[str]):
    self._repo = repo
    self._pr_number = pr_number
    self._target_commit = target_commit
    self._users = users
    self._pr_json = util.request(self._base_pr_url()).json()

    # Hash from user names to booleans representing whether the user has
    # approved or rejected the PR.
    self.reviews = self._calculate_reviews()

    if self.author() in users:
      self.reviews[self.author()] = True

    self.approvals: List[str] = []
    self.rejections: List[str] = []
    for user in users:
      if user in self.reviews:
        if self.reviews[user]:
          self.approvals.append(user)
        else:
          self.rejections.append(user)

    self.non_participants = [ user for user in users
                              if user not in self.approvals
                              and user not in self.rejections ]

  def created_at_ts(self) -> int:
    return util.iso8601_to_ts(self._pr_json['created_at'])

  def pushed_at_ts(self) -> int:
    return util.iso8601_to_ts(self._pr_json['head']['repo']['pushed_at'])

  def last_changed_ts(self) -> int:
    return max(self.created_at_ts(),
               self.pushed_at_ts())

  def days_since_created(self) -> int:
    return util.days_since(self.created_at_ts())

  def days_since_pushed(self) -> int:
    return util.days_since(self.pushed_at_ts())

  def days_since_changed(self) -> int:
    return util.days_since(self.last_changed_ts())

  def _calculate_reviews(self) -> Dict[str, bool]:
    base_url = '%s/reviews' % self._base_pr_url()
    url = base_url
    reviews: Dict[str, bool] = {}
  
    while True:
      response = util.request(url)
  
      for review in response.json():
        user = review['user']['login']
        commit = review['commit_id']
        state = review['state']
  
        if state == 'APPROVED' and commit != self._target_commit:
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
  
        reviews[user] = (state == 'APPROVED')
  
      if 'next' in response.links:
        # This unfortunately points to GitHub, and not to the rate-limit-avoiding
        # proxy.  Pull off the query string (ex: "?page=3") and append that to
        # our url that goes via the proxy.
        next_url = response.links['next']['url']
        github_api_path, query_string = next_url.split('?')
        url = '%s?%s' % (base_url, query_string)
      else:
        return reviews

  def _base_pr_url(self) -> str:
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
    #   location /nomic-github/repos/jeffkaufman/nomic/pulls {
    #     if ($request_method != GET) {
    #       return 403;
    #     }
    #
    #     proxy_cache github-proxy;
    #     proxy_ignore_headers Cache-Control Vary;
    #     proxy_cache_valid any 1m;
    #     proxy_pass https://api.github.com/repos/jeffkaufman/nomic/pulls;
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
      self._repo, self._pr_number)

  def diff(self) -> unidiff.PatchSet:
    response = util.request('https://patch-diff.githubusercontent.com/raw/%s/pull/%s.diff' % (
        self._repo, self._pr_number))
    return unidiff.PatchSet(response.content.decode('utf-8'))

  def author(self) -> str:
    return self._pr_json['user']['login']



