"""
Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
преобразовать результаты из байтовового в строковый тип на кириллице.
"""
import subprocess
import chardet


def ping(domain: str) -> None:
    command = subprocess.Popen(["ping", "-c 5", domain], stdout=subprocess.PIPE)
    for answer in command.stdout:
        encoding = chardet.detect(answer)
        to_console = answer.decode(encoding=encoding["encoding"]).encode("utf-8")
        print(to_console.decode("utf-8").strip())


def main():
    domains = ("yandex.ru", "youtube.com")
    for domain in domains:
        print('-' * 100)
        ping(domain)


if __name__ == '__main__':
    main()
