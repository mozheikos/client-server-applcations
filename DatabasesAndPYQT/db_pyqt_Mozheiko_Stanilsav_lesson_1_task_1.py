"""Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью
функции ip_address()."""

import subprocess
import ipaddress
from typing import List, Tuple, Union


def check_address(address: str) -> bool:
    split_address = address.split('.')
    return all(map(lambda x: x.isdigit() and len(x) <= 3, split_address)) and len(split_address) == 4


def get_ip_by_domain(domain: str) -> str:
    address = subprocess.run(['dig', domain, '+short'], stdout=subprocess.PIPE)
    return address.stdout.decode().split('\n')[0]


def create_ipv4_address(address: str) -> ipaddress.IPv4Address:
    if not check_address(address):
        address = get_ip_by_domain(address)
    return ipaddress.ip_address(address)


def host_ping(
        addresses: List[Union[str, ipaddress.IPv4Address]], iters: int = 3, printing: bool = True
) -> List[Tuple[str, bool]]:

    result = []

    program = 'ping'
    for address in addresses:

        if isinstance(address, str):
            arg = create_ipv4_address(address)
        else:
            arg = address

        ping = subprocess.Popen(
            args=[program, f'-c {iters}', str(arg)],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE
        )
        ping_result = ping.communicate()[0].decode()
        try:
            ping_result = ping_result.split('\n')[-3].split(',')[-2].strip()
        except IndexError:
            print(address, ping_result)
        else:
            reachable = True
            msg = 'доступен'
            if ping_result.startswith('100'):
                reachable = False
                msg = 'недоступен'

            result.append((address, reachable))
            if printing:
                print(f"{address} Узел {msg}")

    return result


if __name__ == '__main__':
    host_ping(['192.168.0.13', '192.168.0.20', 'www.yandex.ru'])
