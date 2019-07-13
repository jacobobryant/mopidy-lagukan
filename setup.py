from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-Lagukan',
    version=get_version('mopidy_lagukan/__init__.py'),
    url='https://github.com/jacobobryant/mopidy-lagukan',
    license='Apache License, Version 2.0',
    author='Jacob O\'Bryant',
    author_email='foo@jacobobryant.com',
    description='Mopidy extension for Lagukan',
    long_description=open('README.md').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
        'appdirs',
        'edn_format',
        'frozendict'
    ],
    entry_points={
        'mopidy.ext': [
            'lagukan = mopidy_lagukan:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
