STEALTH Validation Service []
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

 * Standalone Auth Service

    Start it up:

        authserv

    APIs:

        curl -X GET -i  -H "X-PROJECT-ID: THE_USER_PROJECT_ID_HERE"   127.0.0.1:8000; echo
        curl -X GET -i  -H "X-PROJECT-ID: THE_USER_PROJECT_ID_HERE"  -H "X-AUTH-TOKEN: THE_USER_AUTH_TOKEN_HERE"  127.0.0.1:8000; echo


 * Stealth Auth Endpoint

    APIs:

        curl -X GET -i  127.0.0.1:8080/auth/{THE_USER_PROJECT_ID_HERE}; echo
        curl -X GET -i  -H "X-AUTH-TOKEN: THE_USER_AUTH_TOKEN_HERE"   127.0.0.1:8080/auth/{THE_USER_PROJECT_ID_HERE}; echo



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

    Start up the service by two ways.

        stealth-server
        authserv
        gunicorn auth-middleware:app

    Test command.
        curl -H "X-PROJECT-ID: {project-id}" -v 127.0.0.1:8080/auth
        curl -H "X-PROJECT-ID: {project-id}" -H "X-AUTH-TOKEN: {previously-returned-token}" -v 127.0.0.1:8080/auth




