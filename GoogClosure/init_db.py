import os
import pickle
import time
import re
import sys
import config
import tree_builder

init_db = sys.modules[__name__]

parse_deps_regex = re.compile("^goog\.addDependency\('([^']+)'\, \[([^\]]+)\], \[([^\]]+)\]\);")


def validate_path(path):
  if not(os.path.exists(path)):
    raise Exception("Could not find path: {0}".format(path))


def background_init_database(status, basejs_file, roots, deps_paths):
  config.log.debug("Initialising Google Closure Caches")
  status.set("Initialising Google Closure Caches")

  try:
    init_db._background_init_database_impl(basejs_file, roots, deps_paths)
  except:
    config.initialising = False
    raise

  config.log.debug("Initialising Google Closure Caches - Done")
  status.erase()


def _background_init_database_impl(basejs_file, roots, deps_paths):
  goog_deps = os.path.normpath(os.path.join(os.path.dirname(basejs_file), "deps.js"))
  config.all_dependency_files = deps_paths
  config.all_dependency_files.insert(0, goog_deps)
  config.log.debug("all_dependencies to initialise: {0}".format(config.all_dependency_files))

  if os.path.exists("goog_closure_autocomplete.db"):
    with open("goog_closure_autocomplete.db", "r") as file:
      config.db = pickle.load(file)
      config.log.debug("Database loaded from 'goog_closure_autocomplete.db'")

  config.db = {
    "dependencies": {},
    "deps_files": {},
    "deps_tree": {}
  }

  init_db._cache_all_deps(basejs_file, roots)
  config.db["timestamp"] = time.localtime()
  init_db._dump_caches()


def _dump_caches():
  with open("goog_closure_autocomplete.db", "wb") as file:
    pickle.dump(config.db, file)


def _file_time(file):
  return time.localtime(os.path.getmtime(file))


def _cache_all_deps(basejs_file, roots):
  time_cached = None if not("timestamp" in config.db) else config.db["timestamp"]
  for deps_file_name in config.all_dependency_files:
    config.log.debug("Caching dependencies file: {0}".format(deps_file_name))
    if time_cached == None or init_db._file_time(deps_file_name) > time_cached:
      init_db._parse_deps_file(basejs_file, roots, deps_file_name)
    else:
      init_db._check_dependency_files_timestamps(deps_file_name)


def _parse_deps_file(basejs_file, roots, deps_file_name):
  config.log.debug("Parsing the full dependencies file: {0}".format(deps_file_name))
  deps_files = []
  with open(deps_file_name, "r") as file:
    for line in file:
      js_file = init_db._parse_deps_file_line(basejs_file, roots, line)
      if js_file:
        deps_files.append(js_file)
  config.db["deps_files"][deps_file_name] = deps_files
  tree_builder.add_all_files_to_tree(deps_files)


def _check_dependency_files_timestamps(deps_file_name):
  deps_files = config.db["deps_files"][deps_file_name]
  now = time.localtime()
  for js_file in deps_files:
    file_details = config.db["dependencies"][js_file]
    _file_time = init_db.gmt__file_time(js_file)
    cached_time = file_details["timestamp"]
    if cached_time >= _file_time:
      continue
    file_details["timestamp"] = now
    tree_builder.add_file_members_to_tree(file_details["namespaces_provided"], file_details["js_file"])


def _parse_deps_file_line(basejs_file, roots, line, must_exist=True):
  match = parse_deps_regex.match(line)
  if not(match):
    return None

  js_file = tree_builder.get_real_path_for_file(basejs_file, roots, match.group(1), must_exist)
  if js_file == None:
    return None

  namespaces_provided = match.group(2).replace("'", "").replace(" ", "").split(",")
  tree_builder.add_namespaces_to_tree(namespaces_provided)
  namespaces_required = match.group(3).replace("'", "").replace(" ", "").split(",")

  config.db["dependencies"][js_file] = {
    "timestamp": time.localtime(),
    "namespaces_provided": namespaces_provided,
    "namespaces_required": namespaces_required
  }

  return js_file
