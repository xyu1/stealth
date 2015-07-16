import stealth.util.log as logging
from stealth.transport.wsgi import Driver

app_container = Driver()
logging.setup()
app = app_container.app
