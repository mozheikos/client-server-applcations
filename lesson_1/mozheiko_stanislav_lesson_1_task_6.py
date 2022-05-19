"""
Создать  НЕ программно (вручную) текстовый файл test_file.txt, заполнить его тремя строками:
«сетевое программирование», «сокет», «декоратор».

Принудительно программно открыть файл в формате Unicode и вывести его содержимое.
Что это значит? Это значит, что при чтении файла вы должны явно указать кодировку utf-8
и файл должен открыться у ЛЮБОГО!!! человека при запуске вашего скрипта.

При сдаче задания в папке должен лежать текстовый файл!

Это значит вы должны предусмотреть случай, что вы по дефолту записали файл в cp1251,
а прочитать пытаетесь в utf-8.

Преподаватель будет запускать ваш скрипт и ошибок НЕ ДОЛЖНО появиться!
"""
from typing import Union, List
import chardet


def decoding(filename: str, to_file: bool = False) -> Union[None, List[str]]:
    with open(filename, 'rb') as f:
        detector = chardet.universaldetector.UniversalDetector()
        file = f.readlines()
        for line in file:
            detector.feed(line)
            if detector.done:
                break
        detector.close()
        encoding = detector.result
        if to_file:
            lines = []
            for line in file:
                lines.append(
                    line.decode(encoding=encoding["encoding"])
                )
            return lines
        else:
            print(f'Кодировка: {encoding["encoding"]}\nСодержимое:')
            for line in file:
                line = line.decode(encoding=encoding['encoding'])
                print(line.strip())
            print('-' * 100)


def recode_test_file() -> None:
    content = decoding(filename="test_file.txt", to_file=True)
    with open("test_file.txt", 'w', encoding='utf-8') as f:
        f.writelines(content)


def main():
    """Я был не совсем уверен, нужно ли вывести на экран содержимое файла так, чтобы он правильно прочитался
    вне зависимости от кодировки, или перекодировать файл так, чтобы он правильно читался в любой системе, поэтому
    сделал оба варианта"""
    files = (
        'task_6_cp1251.txt',
        'task_6_utf-8.txt',
        'task_6_koi8.txt'
    )
    for file in files:
        print(f"Чтение {file}")
        decoding(file)
    recode_test_file()


if __name__ == '__main__':
    main()
