from stealth.common import cli
from stealth.transport.wsgi.driver import Driver


@cli.runnable
def run():
    app_container = Driver()
    app_container.listen()
