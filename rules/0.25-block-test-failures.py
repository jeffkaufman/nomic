import os
import runpy

SIMPLE_TESTS = {
    '0.3-allow-points-transfer.py': [
        ('33', 'All file changes must be additions'),
        ('82', 'Points transfer PRs should not add users: got dchudz'),
        ('220', None),
    ],
}


def run_test(pr_number, derived_pr, rule_fname, expected_result):
    _, allow_block, _ = rule_fname.split('-', 2)
    fn_name = 'should_allow' if (allow_block == 'allow') else 'should_block'
    print('TEST %s:%s(%s)' % (rule_fname, fn_name, pr_number))

    rule_py = runpy.run_path(os.path.join('rules/', rule_fname))
    fn = rule_py[fn_name]

    try:
        fn(derived_pr)
    except Exception as e:
        if str(e) != expected_result:
            raise Exception('expected "%s" got "%s"' % (expected_result, e))
        return

    if expected_result:
        raise Exception('expected "%s" but no error was raised')


def should_block(pr):
    # run tests, raise an exception if any fail

    # Cache calls to derive_pr because they're expensive.
    derived_prs = {}

    for rule_fname, tests in SIMPLE_TESTS.items():
        for pr_number, expected_result in tests:
            if pr_number not in derived_prs:
                derived_prs[pr_number] = pr.derive_pr(pr_number)
            derived_pr = derived_prs[pr_number]

            run_test(pr_number, derived_pr, rule_fname, expected_result)
