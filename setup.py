from setuptools import setup

setup(
    name='LexicalDB',
    packages=['LexicalDB'],
    include_package_data=True,
    install_requires=[
        'flask', 'nltk'
    ],
)