def encode_word(word: str, convert: bool) -> None:
    if convert:
        word = word.encode("unicode-escape")
    print(f"{word = }\n{type(word) = }")


def main() -> None:
    """
     Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и проверить тип и содержание
     соответствующих переменных. Затем с помощью онлайн-конвертера преобразовать строковые представление в формат
     Unicode и также проверить тип и содержимое переменных.
    """

    words = (
        "разработка",
        "сокет",
        "декоратор"
    )

    print("String representation:")
    for word in words:
        encode_word(word=word, convert=False)
    print()
    print("Unicode representation:")
    for word in words:
        encode_word(word=word, convert=True)


if __name__ == '__main__':
    main()
