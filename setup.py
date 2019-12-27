from setuptools import find_packages, setup


setup(
    name='Delirium',
    version='0.2',
    description='Delirium fake DNS server',
    license='LICENSE',
    packages=find_packages(),
    install_requires=[
        'dnslib',
        'ipaddress',
        'click',
    ],
    entry_points={
        'console_scripts': [
            'delirium = delirium.apps:delirium',
        ],
    }
)
