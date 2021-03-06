#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Xuan Yu xuanyu1@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
                'python-dateutil', 'python-keystoneclient', 'oslo.utils',
                'oslo.config', 'redis',
                'simplejson', 'd2to1', 'hiredis', 'msgpack-python']
    setup(
        name='stealth',
        version='0.9',
        description='Openstack Keystone Impersonation Token Assignment and Validation Middleware',
        license='Apache License 2.0',
        url='https://github.com/xyu1/stealth',
        download_url = 'https://github.com/xyu1/stealth/tarball/0.9',
        author='Rackspace',
        author_email='xuanyu1@yahoo.com',
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
            'stealth/bin/stealth-middleware.py',
            'stealth/bin/stealth-serv'
        ],
        packages=find_packages(exclude=['tests*'])
    )
