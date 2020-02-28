from setuptools import find_packages, setup


setup(
    name='Delirium',
    version='0.3.0',
    description='Delirium fake DNS server',
    license='LICENSE',
    packages=find_packages(),
    install_requires=[
        'dnslib',
        'ipaddress',
        'sqlalchemy',
        'click',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'delirium = delirium.apps:delirium',
        ],
    }
)
