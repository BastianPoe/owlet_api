#!/usr/bin/env python

from setuptools import setup, find_packages

name='owlet_api'
version='0.1.0'

setup(name = name,
        version = version,
        description = 'Owlet Smart Baby Monitor Inofficial Python API',
        long_description = 'Owlet Smart Baby Monitor Inofficial Python API',
        author = 'Wolf-Bastian Pöttner',
        author_email = 'bastian+owlet@poettner.de',
        packages = ['owlet_api'],
        url = 'https://github.com/BastianPoe/owlet_api/',
        license = 'LGPLv2+',
        classifiers = [
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        keywords = 'owlet baby monitor',
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