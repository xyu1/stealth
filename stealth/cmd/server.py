import stealth.util.log as logging
from stealth.common import cli
from stealth.transport.wsgi.driver import Driver


@cli.runnable
def run():
    logging.setup()
    app_container = Driver()
    app_container.listen()
