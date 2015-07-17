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

        virtualenv -p /usr/bin/python3.4 stealth
        cd stealth
        git clone https://github.com/xyu1/stealth.git
        . bin/activate
        cd stealth
        python setup.py develop

    Copy over config files:

        mkdir ~/.stealth
        cp ini/config.ini ~/.stealth/config.ini

    Start it up:

        stealth-server

