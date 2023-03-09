import threading

test_lock = threading.Lock()

def child_thread():
    global test_lock
    print('child: aquire attempt')
    test_lock.acquire()
    print('child: aquired lock')
    test_lock.release()

print('parent: aquired lock')
test_lock.acquire()
tmp_thread = threading.Thread(target=child_thread)
tmp_thread.start()
input('Press Enter to release lock')
test_lock.release()