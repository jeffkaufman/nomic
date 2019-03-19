from typing import Dict, List, Optional, Tuple
import subprocess
import unidiff
import shutil
import os
import util


class PullRequest:
    def __init__(self, repo: str, pr_number: str, target_commit: str, users: List[str]):
        self._repo = repo
        self._pr_number = pr_number
        self._target_commit = target_commit
        self._users = users
        self._pr_json = util.request(self._base_pr_url()).json()
        self._clone_url = self._pr_json['head']['repo']['clone_url']
        self._ref = self._pr_json['head']['ref']

        # commit hash -> diff at commit; lazily built
        self._commit_diffs: Dict[str, str] = {}

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

        self.non_participants = [user for user in users
                                 if user not in self.approvals
                                 and user not in self.rejections]

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

    def _calculate_diff_at_commit(self, commit: str) -> str:
        # Determine what changes this commit makes relative to master.
        #
        # I don't know a git command directly for it, so instead make a temporary
        # repo, load all relevant commits into the repo, merge the commit in
        # question into master, and then diff against origin/master.

        print('Calculating diff at %s' % commit)
        original_working_directory = os.getcwd()
        tmp_repo_fname = 'tmp-repo'
        try:
            # Make a new clone to work in.
            subprocess.check_call([
                'git', 'clone',
                'https://github.com/%s.git' % self._repo, tmp_repo_fname])
            os.chdir(tmp_repo_fname)
            remote_name = self.author()

            # We can't refer to commit until we download it.
            subprocess.check_call(['git', 'remote', 'add', remote_name, self._clone_url])
            subprocess.check_call(['git', 'fetch', remote_name, self._ref])
            subprocess.check_call(['git', 'merge', '--no-edit', commit])

            completed_process = subprocess.run(
                ['git', 'diff', 'origin/master'], stdout=subprocess.PIPE)
            if completed_process.returncode != 0:
                raise Exception(completed_process)

            return completed_process.stdout.decode('utf-8')

        except Exception:
            print('Failed to get diff at %s' % commit)
            return ''

        finally:
            # This runs even if we return above, and puts us back in the state we
            # were in before we tried to calculate the diff.

            os.chdir(original_working_directory)
            if os.path.exists(tmp_repo_fname):

                # rmtree can fail on Windows if files are set to readonly
                def remove_readonly(func, path, _):
                    # Clear the readonly bit and reattempt the removal
                    os.chmod(path, stat.S_IWRITE)
                    func(path)

                shutil.rmtree(tmp_repo_fname, onerror=remove_readonly)

    def _diff_at_commit(self, commit: str) -> str:
        if commit not in self._commit_diffs:
            self._commit_diffs[commit] = self._calculate_diff_at_commit(commit)

        return self._commit_diffs[commit]

    def _pr_diff_identical(self, commit_a: str, commit_b: str) -> bool:
        diff_a = self._diff_at_commit(commit_a)
        diff_b = self._diff_at_commit(commit_b)

        if not diff_a or not diff_b:
            return False

        return diff_a == diff_b

    def _calculate_reviews(self) -> Dict[str, bool]:
        base_url = '%s/reviews' % self._base_pr_url()
        url = base_url

        # List of reviews in the order they were given.
        raw_reviews: List[Tuple[str, str, str]] = []

        reviews: Dict[str, bool] = {}  # username -> bool approved

        while True:
            response = util.request(url)

            for review in response.json():
                user = review['user']['login']
                if user not in self._users:
                    continue
                raw_reviews.append((user,
                                    review['state'],
                                    review['commit_id']))

            if 'next' in response.links:
                # This unfortunately points to GitHub, and not to the rate-limit-avoiding
                # proxy.  Pull off the query string (ex: "?page=3") and append that to
                # our url that goes via the proxy.
                next_url = response.links['next']['url']
                github_api_path, query_string = next_url.split('?')
                url = '%s?%s' % (base_url, query_string)
            else:
                break

        for user, state, commit in reversed(raw_reviews):
            # Iterate through reviews in reverse chronological order, most recent
            # first.

            if user in reviews:
                # Already have a judgement from this user on this PR.
                continue

            if state == 'COMMENTED':
                pass  # Ignore comments

            elif state == 'APPROVED':
                if commit == self._target_commit:
                    reviews[user] = True
                elif self._pr_diff_identical(commit, self._target_commit):
                    print('Determined approval by %s at old commit %s should still count'
                          ' for %s' % (user, commit, self._target_commit))
                    reviews[user] = True
                else:
                    print('Old approval by %s at %s not valid at %s' % (
                        user, commit, self._target_commit))

            else:
                reviews[user] = False

        return reviews

    def _base_pr_url(self, pr_number: Optional[str] = None) -> str:
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
        # world-accessible it could potentially get hit by substantial traffic.  At a
        # 60s cache and 5k/hr limit we can have 83 GitHub API requests per page
        # render and not go down.  As of 2018-01-18 there are eight open PRs, each
        # of which needs a request to get reviews, so we're ok by a factor of 10.  If
        # we have a lot of old open PRs we don't care about we could either close
        # them or make the dashboard only gather reviews for PRs in the "reviewme"
        # state.
        if pr_number is None:
            pr_number = self._pr_number

        return 'https://www.jefftk.com/nomic-github/repos/%s/pulls/%s' % (
            self._repo, pr_number)

    def derive_pr(self, pr_number: str, target_commit: Optional[str] = None):
        # Load a different PR based on this one.  If the intended commit is not
        # specified, the PR is loaded at HEAD.
        if target_commit is None:
            pr_json = util.request(self._base_pr_url(pr_number)).json()
            target_commit = pr_json['head']['sha']

        return PullRequest(repo=self._repo,
                           pr_number=str(pr_number),
                           target_commit=target_commit,
                           users=self._users)

    def diff(self) -> unidiff.PatchSet:
        response = util.request('https://patch-diff.githubusercontent.com/raw/%s/pull/%s.diff' % (
            self._repo, self._pr_number))
        return unidiff.PatchSet(response.content.decode('utf-8'))

    def get_new_bonuses_or_raise(self) -> List[Tuple[str, str, int]]:
        # If this PR represents adding only new bonus files, return details
        # about the files.  Otherwise raise an exception explaining how the diff
        # doesn't qualify.
        #
        # Returns [(bonus_1_user, bonus_1_name, bonus_1_value),
        #          (bonus_2_user, bonus_2_name, bonus_2_value), ... ]

        diff = self.diff()
        if diff.modified_files or diff.removed_files:
            raise Exception('All file changes must be additions')

        bonuses: List[Tuple[str, str, int]] = []

        for added_file in diff.added_files:
            s_players, points_user, s_bonuses, bonus_name = added_file.path.split('/')
            if s_players != 'players' or s_bonuses != 'bonuses':
                raise Exception('Added file %s is not a bonus file' % added_file)

            (diff_invocation_line, file_mode_line, _, removed_file_line,
             added_file_line, patch_location_line, file_delta_line,
             empty_line) = str(added_file).split('\n')

            if diff_invocation_line != 'diff --git a/%s b/%s' % (added_file.path, added_file.path):
                raise Exception('Unexpected diff invocation: %s' % diff_invocation_line)

            if file_mode_line != 'new file mode 100644':
                raise Exception('File added with incorrect mode: %s' % file_mode_line)

            if removed_file_line != '--- /dev/null':
                raise Exception(
                    'Diff format makes no sense: added files should say they are from /dev/null')

            if added_file_line != '+++ b/%s' % added_file.path:
                raise Exception('Something wrong with file adding line: file is '
                                '%s but got %s' % (added_file.path, added_file_line))

            if patch_location_line != '@@ -0,0 +1,1 @@':
                raise Exception('Patch location makes no sense: %s' %
                                patch_location_line)

            if empty_line:
                raise Exception('Last line should be empty')

            if file_delta_line.startswith('+'):
                actual_file_delta = file_delta_line[1:]
            else:
                raise Exception('File delta missing initial + for addition: %s' %
                                file_delta_line)

            try:
                points_change = int(actual_file_delta)
            except Exception:
                raise Exception("File should contain a single integer.")

            bonuses.append((points_user, bonus_name, points_change))

        if not bonuses:
            raise Exception('No bonus files created')

        return bonuses

    def author(self) -> str:
        return self._pr_json['user']['login']
