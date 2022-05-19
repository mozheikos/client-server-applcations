"""
3. Задание на закрепление знаний по модулю yaml.
 Написать скрипт, автоматизирующий сохранение данных
 в файле YAML-формата.
Для этого:

Подготовить данные для записи в виде словаря, в котором
первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа —
это целое число с юникод-символом, отсутствующим в кодировке
ASCII(например, €);

Реализовать сохранение данных в файл формата YAML — например,
в файл file.yaml. При этом обеспечить стилизацию файла с помощью
параметра default_flow_style, а также установить возможность работы
с юникодом: allow_unicode = True;

Реализовать считывание данных из созданного файла и проверить,
совпадают ли они с исходными.
"""

import yaml
from pathlib import Path


def write_to_yaml(items: dict):

    data = {
        "items": [],
        "items_price": {
        },
        "items_quantity": len(items.items())
    }
    for key, value in items.items():
        data['items'].append(key)
        data['items_price'][key] = f"{value[0]}{chr(8364)} - {value[1]}{chr(8364)}"

    with open(f"{path}/file.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(data=data, stream=f, allow_unicode=True)

    return read_from_yaml(initial=data)


def read_from_yaml(initial: dict):

    with open(f"{path}/file.yaml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print(initial, type(initial))
    print(data, type(data))
    if initial == data:
        print("Исходный и считанный объекты имеют одинаковое содержимое")
    else:
        print("Ощибка чтения или записи, исходный и считанный объекты не равны")


def main():

    items = {}
    count = int(input("Введите количество позиций для записи: "))
    for i in range(count):
        item = input("Введите название: ")
        price_1 = input(f"Введите минимальную цену в евро для позиции {item}: ")
        price_2 = input(f"Введите максимальную цену в евро для позиции {item}: ")
        items[item] = (price_1, price_2)

    write_to_yaml(items=items)


if __name__ == '__main__':
    path = Path(__file__).resolve().parent
    main()
