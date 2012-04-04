import logging

# Globals
initialising = False
TESTING = True
db = None
SETTINGS = ["basejs_file", "deps_paths", "roots"]
log = logging.getLogger('goog_closure')
all_dependency_files = []


def initialise_logger():
  file_logger = logging.FileHandler('googcloure.log')
  file_logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  file_logger.setFormatter(formatter)
  log.addHandler(file_logger)
  log.setLevel(logging.DEBUG)


def init():
  if not(log.isEnabledFor(logging.DEBUG)):
    initialise_logger()

init()

log.info('Google Closure Sublime Plugin - config initialised')
