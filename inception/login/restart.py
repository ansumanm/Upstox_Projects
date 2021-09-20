"""
Exec ourselves.
"""
import sys
import os
import copy
from time import sleep
"""
Usage: python3 test.py 1 20
"""
def get_last_restart_delay():
    try:
        with open(".last_restart_sec", "r") as f:
            return int(f.read())
    except Exception as e:
        return 2

def set_last_restart_delay(delay):
    try:
        with open(".last_restart_sec", "w") as f:
            return int(f.write("{}".format(delay)))
    except Exception as e:
        print("Could not set delay. Exiting...")
        sys.exit(0)

def main():
    print("""
    Process pid: {}
    """.format(os.getpid()))
    print(sys.argv[0])
    print(sys.argv[1])
    print(sys.argv[2])

    arg = int(sys.argv[1])
    count = int(sys.argv[2])

    if arg >= count:
        sys.exit(0)

    cmd = copy.deepcopy(sys.argv)
    cmd[1] = str(arg + 1)
    cmd.insert(0,'python3')
    delay = get_last_restart_delay()
    set_last_restart_delay(delay*delay)
    print("Delay: {} secs".format(delay))
    sleep(delay)
    os.execvp(cmd[0], cmd)


if __name__ == '__main__':
    main()

