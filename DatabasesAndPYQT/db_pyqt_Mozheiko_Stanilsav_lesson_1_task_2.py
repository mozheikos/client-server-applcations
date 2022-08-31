import ipaddress
from typing import Union, Tuple, List

from DatabasesAndPYQT.db_pyqt_Mozheiko_Stanilsav_lesson_1_task_1 import host_ping


def host_range_ping(address_range: Tuple[str, str], printing: bool = True) -> List[Tuple[str, bool]]:

    start = ipaddress.ip_address(address_range[0])
    addresses = [start]
    if isinstance(address_range[1], str):
        end = ipaddress.ip_address(address_range[1])

        while start < end:
            start += 1
            addresses.append(start)

    return host_ping(addresses, printing=printing)


if __name__ == '__main__':
    host_range_ping(('192.168.0.1', '192.168.0.13'))
