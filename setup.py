#!/usr/bin./env python

from setuptools import find_packages, setup


setup(
    name='Delirium',
    version='0.0rc1',
    description='Delirium fake DNS server',
    license='LICENSE',
    packages=find_packages(),
    install_requires=[
        'dnslib',
        'enum34',
        'ipaddress',
    ],
    entry_points={
        'console_scripts': [
            'delirium = delirium.delirium:main',
        ],
    }
)
