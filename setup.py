#!/usr/bin/env python
# coding: utf8

from setuptools import setup, find_packages

name='owlet_api'
version='0.1.0'

setup(name = name,
        version = version,
        description = 'Unofficial Python API for the Owlet Smart Baby Monitor',
        long_description = 'Unofficial Python API for the Owlet Smart Baby Monitor',
        author = 'Wolf-Bastian Pöttner',
        author_email = 'bastian+owlet@poettner.de',
        packages = ['owlet_api'],
        url = 'https://github.com/BastianPoe/owlet_api/',
        license = 'MIT',
        classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        keywords = 'owlet baby monitor api ayla',
        install_requires = [
            'requests',
            'python-dateutil',
            'argparse'
        ],
        entry_points = {
            'console_scripts': [
                'owlet=owlet_api.cli:cli',
            ]
        },
        test_suite = 'tests',
        include_package_data = True,
)

