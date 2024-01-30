import argparse
import logging, sys
from gunicorn.app.base import BaseApplication
#from code_vessel.servers import app
from code_vessel.servers.main_server import app

# initiate logger
logger        = logging.getLogger()
formatter     = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s")
stdoutHandler = logging.StreamHandler(sys.stdout)
stdoutHandler.setLevel(logging.DEBUG)
stdoutHandler.setFormatter(formatter)
logger.addHandler(stdoutHandler)

parser = argparse.ArgumentParser(description='Run a Flask application with a custom port.')
parser.add_argument('--host',    type=str, required = False, default = "0.0.0.0", help='Host to run the Flask app on')
parser.add_argument('--port',    type=int, required = False, default = 5000,      help='Port number to run the Flask app on')
parser.add_argument('--workers', type=int, required = False, default = 4,         help='Number of workers')

class FlaskApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application

def run():
    args = parser.parse_args()

    gunicorn_options = {
        'bind': '{host}:{port}'.format(host=args.host, port=str(args.port)),
        'workers': args.workers,  # Adjust the number of workers as needed
    }

    FlaskApplication(app, gunicorn_options).run()
