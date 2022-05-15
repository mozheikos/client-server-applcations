"""
Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность кодов
(не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.
"""


def main() -> None:
    words = (
        b"class",
        b"functions",
        b"method"
    )
    for word in words:
        print(f"word: {word}\n{len(word) = }\n{type(word) = }\n")


if __name__ == '__main__':
    main()
