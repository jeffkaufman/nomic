import pep8

def should_block(pr):
  pep8style = pep8.StyleGuide(quiet=True)
  result = pep8style.check_files('.')
  if result.total_errors > 0
    raise Exception('pep8 failed')
