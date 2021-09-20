import signal
import threading
import time

def signal_handler_function(signum, frame):
    print("Signal handler..%d. Exiting.." % signum)
    sys.exit(0)
    

def do_nothing():
    try:
        while True:
            print("Thread: Going to sleep...")
            time.sleep(5)
    except:
        print("Thread exiting..")
        sys.exit(0)

def main():
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler_function)

    t = threading.Thread(target=do_nothing)
    t.start()

    print("Main: Waiting for 5 sec..")
    time.sleep(5)

    for thread in threading.enumerate():
        print(str(thread))
        print(thread.ident, thread.name)
        if thread.name != 'MainThread':
            # Raise a signal to the child thread...
            # print("Sending signal to thread.. %d" % thread.ident)
            # signal.pthread_kill(thread.ident, signal.SIGTERM)

            # Raise a runtime exception..
            thread.daemon = True

    t.join()
    print("Finally main exits...")


main()
