"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку определенных данных из файлов
info_1.txt, info_2.txt, info_3.txt и формирующий новый «отчетный» файл в формате CSV. Для этого:
Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных.
В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения каждого параметра поместить в
соответствующий список. Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list,
os_type_list. В этой же функции создать главный список для хранения данных отчета — например, main_data — и поместить в
него названия столбцов отчета в виде списка: «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла);
Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой функции реализовать получение данных
через вызов функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл;
Проверить работу программы через вызов функции write_to_csv().
"""
import chardet
from collections import Counter
import csv
from pathlib import Path


def detect_encoding(filename: str) -> str:
    """У Вас файлы в cp-1251, а у меня линукс. Конечно я мог просто перекодировать утилитой recode, или захардкодить
    открытие файла с кодировкой cp-1251, но так не интересно.
    Решил воспользоваться chardet. Но и тут веселость: чардет каждую строку детектирует в разную кодировку, в итоге
    некоторые символы неправильно читаются, а если использовать UniversalDetector модуля chardet - он возвращает None,
    видимо не может определиться. Пришлось поплясать с бубном, но вроде ничего, работает"""

    with open(f'{filename}', 'rb') as f:
        data = f.readlines()
        encoding_detect = []
        for line in data:
            encoding = chardet.detect(line)['encoding']
            encoding_detect.append(encoding)
        """Проверил кодировку каждой строки и взял ту, которая чаще всего встречается"""
        count = Counter(encoding_detect)
        encoding = count.most_common(1)[0][0]
        return encoding


def get_data(filename: str, keys: list) -> dict:

    encoding = detect_encoding(filename=filename)
    with open(f'{filename}', 'r', encoding=encoding) as f:
        file_data = f.readlines()
        data = dict.fromkeys(keys, str)
        for line in file_data:
            if line.find(":") == -1:
                continue
            else:
                key, value = line.split(":", 1)
            if key in keys or key == 'Изготовитель ОС':
                data[key.strip()] = value.strip()
        rename_value = data.pop('Изготовитель ОС')
        data['Изготовитель системы'] = rename_value
    return data


def write_to_csv(filename: str, filenames: tuple) -> None:
    keys = [
        '№',
        'Изготовитель системы',
        'Название ОС',
        'Код продукта',
        'Тип системы'
    ]
    rows = []
    count = 1
    for file in filenames:
        row = get_data(filename=file, keys=keys)
        row['№'] = count
        rows.append(row)
        count += 1

    with open(f'{path}/{filename}.csv', 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(result_filename: str):
    files = (f'{path}/info_1.txt', f'{path}/info_2.txt', f'{path}/info_3.txt')
    write_to_csv(filename=result_filename, filenames=files)


if __name__ == '__main__':
    path = Path(__file__).resolve().parent
    result_file = input("Please input name of result file: ")
    if result_file.find('.') != -1:
        result_file, _ = result_file.split('.')
    main(result_filename=result_file)
