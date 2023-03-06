import threading as thr

buf = []
def input_thread():
    global buf
    while True:
        buf.append(input('>>> '))

it = thr.Thread(target=input_thread, args=())
it.start()

while True:
    if len(buf) > 0:
        print('message got and handled')
        print("~: ", buf.pop())