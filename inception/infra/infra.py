import logging
import loggerclass
from loggerclass import xlogger_f
from loggerclass import xlogger_ansu
import os
import sys
import tempfile
import signal
import time

#Upstox_Bot_Key_ANSU = "659901268:AAEBYtdSWaN1hhyqiXNRUJj5qgvmIe0ZSmE"
#Chat_ID_ANSU = "336975256"

Upstox_Bot_Key_AKN = "659901268:AAEBYtdSWaN1hhyqiXNRUJj5qgvmIe0ZSmE"
Chat_ID_AKN = "243181507,336975256,688610986"

class Infra:
    def __init__(self, tsb=""):

        #init xlogger
        xlogger_f("../logs/upstox", Chat_ID_AKN, Upstox_Bot_Key_AKN, tsb)
        #xlogger_ansu("../logs/upstox", Chat_ID_ANSU, Upstox_Bot_Key_ANSU, tsb)

        signal.signal(signal.SIGTERM, self.sigterm_handler)
        

    def __del__(self):
        pass

    def sigterm_handler(self, signal, frame):
        # save the state here or do whatever you want
        print('booyah! bye bye')
        self.__del__()
        sys.exit(0)

    def filter_non_printable(self, str):
        ret=""
        for c in str:
            if ord(c) > 31 or ord(c) == 9:
                ret += c
            else:
                ret += " "
        ret = ret.replace("python ", "")
        ret = ret.replace("python3 ", "")
        ret = ret.replace(".py", "")
        return ret
    
    def get_pid_name(self, pid):
        path = '/proc/' +  str(pid) + '/' + 'cmdline'
        try:
            with open(path, 'r') as pidfile:
                return self.filter_non_printable(pidfile.readline())
    
        except Exception:
            print("Error: Cannot find process name")
            pass
            return


    def write_pid_to_pidfile(self, pidfile_path):
        """ Write the PID in the named PID file.
    
            Get the numeric process ID (“PID”) of the current process
            and write it to the named file as a line of text.
    
            """
        open_flags = (os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        open_mode = 0o644
        pidfile_fd = os.open(pidfile_path, open_flags, open_mode)
        pidfile = os.fdopen(pidfile_fd, 'w')
    
        # According to the FHS 2.3 section on PID files in /var/run:
        #
        #   The file must consist of the process identifier in
        #   ASCII-encoded decimal, followed by a newline character. For
        #   example, if crond was process number 25, /var/run/crond.pid
        #   would contain three characters: two, five, and newline.
    
        pid = os.getpid()
        pidfile.write("%s\n" % pid)
        pidfile.close() 



