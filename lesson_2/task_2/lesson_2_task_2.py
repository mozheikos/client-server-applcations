import datetime
import json
from pathlib import Path


def write_order_to_json(item: str, quantity: int, price: str, buyer: str, data: datetime.date):
    data_dict = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'data': str(data)
    }

    with open(f'{path}/orders.json', 'r+', encoding='utf-8') as f:
        start = f",\n{' ' * 8}"
        end = f"\n{' ' * 4}]\n"
        close = '}'
        data_to_write = json.dumps(data_dict, ensure_ascii=False, indent=12)

        to_write = start + data_to_write + end + close

        position = 0
        for line in f.readlines():
            if line.find(']') != -1:
                position = line.find(']')
                break

        to_write = to_write.replace('}', '        }', 1)
        if position == 15:
            f.seek(f.tell() - 3, 0)
            f.write(to_write[1:])
        else:
            f.seek(f.tell() - 8, 0)
            f.write(to_write)


def main():
    item = input("Введите наименование: ")
    quantity = int(input("Введите количество: "))
    price = f'{input("Введите стоимость в евро: ")} {chr(8364)}'
    buyer = input("Введите имя покупателя: ")
    data = datetime.date.today()
    write_order_to_json(item, quantity, price, buyer, data)


if __name__ == '__main__':
    path = Path(__file__).resolve().parent
    main()
