from stealth.transport.wsgi.v1_0 import controller_auth


def public_endpoints():

    return [

        ('/auth',
         controller_auth.ItemResource()),

    ]
