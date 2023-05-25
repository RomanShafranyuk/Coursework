from random import randint
import json


def generate_timetable(username, timespan_start, timespan_end, times, pause_len = 5):
    minute_span = (timespan_end - timespan_start) * 60
    piece = minute_span / times
    tt = []
    for i in range(times):
        st_time = int(piece*i) + randint(0, int(piece - pause_len))
        tt.append(st_time)
    res = []
    for i in tt:
        res.append([timespan_start + int(i // 60), i % 60])
    with open(f'timetable_{username}.json', 'w') as f:
        json.dump({'pause_len': pause_len, 'data': res}, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    generate_timetable('dimadivan1', 14, 20, 7)