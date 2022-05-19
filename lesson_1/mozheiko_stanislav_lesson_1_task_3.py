"""
Определить, какие из слов «attribute», «класс», «функция», «type»
невозможно записать в байтовом типе с помощью маркировки b'' (без encode decode).
"""


def main():
    words = ('attribute', 'класс', 'функция', 'type')
    for word in words:
        try:
            encoded = eval(f"b'{word}'")
        except SyntaxError as e:
            print(f"Слово '{word}' содержит символы, не входящие в кодировку ASCII, "
                  f"его нельзя перевести в байты методом b''")
        else:
            print(encoded)


if __name__ == '__main__':
    main()
