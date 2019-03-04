import os
import copy
import subprocess


def should_block(pr):
    cmd = ['mypy', 'validate.py']
    env = copy.copy(os.environ)
    env['MYPYPATH'] = 'stubs'
    completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, env=env)
    print(completed_process.stdout.decode('utf-8'))
    if completed_process.returncode != 0:
        raise Exception('mypy failed')
