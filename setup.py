# -*- coding: utf-8 -*-
import sys
try:
    from distutils.core import setup
    from setuptools import find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
else:
    REQUIRES = ['configobj', 'falcon', 'six', 'setuptools >= 1.1.6',
                'python-dateutil', 'python-keystoneclient', 'taskflow',
                'redis', 'simplejson', 'd2to1', 'hiredis', 'msgpack-python',
                'kazoo',
                'cassandra-driver', 'stoplight']
    setup(
        name='stealth',
        version='0.1',
        description='',
        license='Apache License 2.0',
        url='',
        author='Rackspace',
        author_email='',
        include_package_data=True,
        install_requires=REQUIRES,
        test_suite='stealth',
        zip_safe=False,
        entry_points={
            'console_scripts': [
                'stealth-server = stealth.cmd.server:run',
            ]
        },
        scripts=[
            'stealth/bin/authserv'
        ],
        packages=find_packages(exclude=['tests*'])
    )
