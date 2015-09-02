STEALTH Validation Middleware []
=====

Impersonation Token Assignment and Validation Service towards Openstack Identity Server


What is STEALTH Validation Service?
--------------
To be created.

API
---
To be created.

Features
--------

 * Authentication Middleware

    Example starts up:

        gunicorn -b 127.0.0.1:8999  stealth-middleware:app

    APIs:

        curl -X GET -i  -H "X-PROJECT-ID: THE_USER_PROJECT_ID_HERE"  -v 127.0.0.1:8999
        curl -X GET -i  -H "X-PROJECT-ID: THE_USER_PROJECT_ID_HERE"  -H "X-AUTH-TOKEN: THE_USER_AUTH_TOKEN_HERE" -v  127.0.0.1:8999

 * Standalone Auth Service

    Start up:

        stealth-serv

    APIs:

        curl -X GET -i  -H "X-PROJECT-ID: THE_USER_PROJECT_ID_HERE"  -v 127.0.0.1:8999
        curl -X GET -i  -H "X-PROJECT-ID: THE_USER_PROJECT_ID_HERE"  -H "X-AUTH-TOKEN: THE_USER_AUTH_TOKEN_HERE" -v 127.0.0.1:8999


 * Stealth Auth Endpoint plug-in for existing service

    Example starts up:

        stealth-server

    APIs:

        curl -X GET -v -i  127.0.0.1:8999/auth/{THE_USER_PROJECT_ID_HERE}
        curl -X GET -v -i  -H "X-AUTH-TOKEN: THE_USER_AUTH_TOKEN_HERE"   127.0.0.1:8999/auth/{THE_USER_PROJECT_ID_HERE}



Installation
------------

    Install the code.

        # Install dependencies.
        sudo apt-get install redis
        sudo apt-get install python-software-properties
        sudo add-apt-repository cloud-archive:[RELEASE_NAME]
        # NOTE(2015-08-19): RELEASE_NAME must be one of ['folsom', 'folsom-proposed', 'grizzly', 'grizzly-proposed', 'havana', 'havana-proposed', 'icehouse', 'icehouse-proposed', 'juno', 'juno-proposed', 'kilo', 'kilo-proposed', 'tools', 'tools-proposed']
        sudo apt-get update
        sudo apt-get install python-oslo.utils python-oslo.config

        # Create the work directory.
        sudo pip install virtualenv --upgrade
        virtualenv -p /usr/bin/python3.4 stealth
        cd stealth
        . bin/activate
        pip install --upgrade netifaces oslo.config oslo.utils
        pip3 uninstall gunicorn
        pip3 install gunicorn


        # Retrieve the latest.
        git clone https://github.com/xyu1/stealth.git
        cd stealth

        pip install --upgrade setuptools

        # Build.
        python setup.py build
        python setup.py install

    Copy over config files and edit.

        mkdir ~/.stealth
        cp ini/config.ini ~/.stealth/config.ini





