import time
import shlex
from subprocess import Popen, PIPE
import random


def get_sys_info():
    while True:
        time.sleep(1)
        yield 'data: ' + str(random.random()) + '\n\n'
