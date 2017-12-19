# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

description = long_descr = 'Mix/scramble RaiBlocks transactions between random local ' +\
                           'accounts before sending to the real destination.'

main_ns = {}
with open('raimixer/version.py') as ver_file:
    exec(ver_file.read(), main_ns)

version = main_ns['__version__']
setup(
    name = 'raimixer',
    version = version,
    description = description,
    long_description = long_descr,
    license = 'GPL 3.0',
    url = 'https://github.com/juanjux/raimixer',
    download_url = 'https://github.com/juanjux/raimixer/archive/%s.tar.gz' % version,
    author = 'Juanjo Alvarez',
    author_email = 'gorthol@protonmail.com',
    packages = find_packages(exclude=['tests']),
    entry_points = {
        'console_scripts': [
            'raimixer = raimixer.cli:main'
        ]
    },
    install_requires = [
          'requests==2.18.4'
    ],
    extras_require = {},
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Security',
        'Topic :: Security :: Cryptography',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6'
    ]
)
