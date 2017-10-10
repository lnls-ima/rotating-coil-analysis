#!/usr/bin/env python3

from setuptools import setup

with open('VERSION', 'r') as _f:
    __version__ = _f.read().strip()

setup(
    name='rotcoil',
    version=__version__,
    author='lnls-ima',
    description='Rotating Coil Package',
    license='MIT License',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
    ],
    packages=['rotcoil'],
    package_data={'rotcoil': ['VERSION']},
    zip_safe=False
)
