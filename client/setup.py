from setuptools import setup, find_packages

setup(
    name='messenger_client_smozheiko',
    version='0.1.0',
    description='Client for messenger',
    author='Mozheiko Stanislav',
    author_email='mozheiko.stanislav@yandex.ru',
    packages=find_packages(),
    requires=['PyQt5', 'sqlalchemy', 'cryptography', 'rsa', 'pydantic']
)