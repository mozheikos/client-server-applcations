from typing import Tuple
from DatabasesAndPYQT.db_pyqt_Mozheiko_Stanilsav_lesson_1_task_2 import host_range_ping
from tabulate import tabulate


def host_range_ping_tab(addresses_range: Tuple[str, str]) -> None:
    result = host_range_ping(addresses_range, printing=False)

    reachable, unreachable = [], []
    for row in result:
        if row[1]:
            reachable.append(row[0])
        else:
            unreachable.append(row[0])

    to_print = []
    i = 0
    length = min(len(reachable), len(unreachable))
    while i < length:
        to_print.append([reachable[i], unreachable[i]])
        i += 1

    if i < len(reachable):
        while i < len(reachable):
            to_print.append([reachable[i], ''])
            i += 1
    else:
        while i < len(unreachable):
            to_print.append(['', unreachable[i]])
            i += 1

    header = ['Reachable', 'Unreachable']
    print(tabulate(to_print, headers=header, tablefmt='fancy_grid', stralign='center'))


if __name__ == '__main__':
    host_range_ping_tab(('192.168.0.1', '192.168.0.15'))
