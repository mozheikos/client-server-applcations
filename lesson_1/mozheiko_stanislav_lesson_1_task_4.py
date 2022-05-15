"""
Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в байтовое и
выполнить обратное преобразование (используя методы encode и decode).
"""


def main() -> None:
    words = (
        "разработка",
        "администрирование",
        "protocol",
        "standard"
    )

    for word in words:
        encoded = word.encode("utf-8")
        print(f"initial word: {word}\nencoded word: {encoded}\n{type(encoded) = }")
        decoded = encoded.decode("utf-8")
        print(f"decoded word: {decoded}\n{type(decoded)}\n")


if __name__ == '__main__':
    main()
