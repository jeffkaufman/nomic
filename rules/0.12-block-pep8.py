import pycodestyle


def should_block(pr):
    style = pycodestyle.StyleGuide(max_line_length=120)
    result = style.check_files('.')
    if result.total_errors > 0:
        raise Exception('pep8 check failed')
