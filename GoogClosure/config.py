import logging
import inspect
import logging.handlers
logging.raiseExceptions = False

# Globals
initialising = False
TESTING = True
db = None
SETTINGS = ["basejs_file", "deps_paths", "roots"]
log = logging.getLogger('goog_closure')
all_dependency_files = []


def initialise_logger():
  if inspect.stack()[-10][1].find('tests'):
    return  # No logging for tests as it causes errors

  file_logger = logging.handlers.RotatingFileHandler('googcloure.log', 'a', 102400, 2)
  file_logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  file_logger.setFormatter(formatter)
  log.addHandler(file_logger)
  log.setLevel(logging.DEBUG)
  pass


def init():
  if not(log.isEnabledFor(logging.DEBUG)):
    initialise_logger()

init()

log.info('Google Closure Sublime Plugin - config initialised')
