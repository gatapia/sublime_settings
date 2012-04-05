import sublime
import sublime_plugin
import os
import pickle
import thread
import threading
import time
import config
import re
import tree_builder

# COMPILED REGEX
parse_deps_regex = re.compile("^goog\.addDependency\('([^']+)'\, \[([^\]]+)\], \[([^\]]+)\]\);")


class GoogClosureInitDatabaseCommand(sublime_plugin.EventListener):

  def on_load(self, view):
    self.init_database(view)

  def init_database(self, view):
    if config.db != None:
      config.log.debug("Database already initialised. Ignoring call to init_database.")
      return

    if config.initialising:
      config.log.debug("Database initialising. Ignoring call to init_database.")
      return

    self._load_and_validate_settings(view)

    a_lock = thread.allocate_lock()
    with a_lock:
      if config.initialising:
        config.log.debug("Database initialising. Ignoring call to init_database.")
        return
      config.initialising = True

    bg_thread = threading.Thread(target=self._background_init_database, args=[view])
    bg_thread.start()

  def _load_and_validate_settings(self, view):
    settings = sublime.load_settings('GoogClosure.sublime-settings')

    for setting in config.SETTINGS:
      print 'setting:', setting, 'value: ', settings.get(setting)
      if not (settings.get(setting)):
        raise Exception("Could not find the setting [{0}] in the settings files.".format(setting))
      view.settings().set(setting, settings.get(setting))

    config.log.debug("All settings loaded.")

  def _background_init_database(self, view):
    config.log.debug("Initialising Google Closure Caches")
    sublime.set_timeout(lambda: view.set_status("googclosure", "Initialising Google Closure Caches"), 0)

    try:
      self._background_init_database_impl(view)
    except:
      config.initialising = False
      raise

    config.log.debug("Initialising Google Closure Caches - Done")
    sublime.set_timeout(lambda: view.erase_status("googclosure"), 0)

  def _background_init_database_impl(self, view):
    basejs_file = view.settings().get("basejs_file")
    goog_deps = os.path.normpath(os.path.join(os.path.dirname(basejs_file), "deps.js"))
    config.all_dependency_files = view.settings().get("deps_paths")
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

    self._cache_all_deps()

    config.db["timestamp"] = time.localtime()
    self._dump_caches()

  def _dump_caches(self):
    with open("goog_closure_autocomplete.db", "wb") as file:
      pickle.dump(config.db, file)

  def _file_time(self, file):
    return time.localtime(os.path.getmtime(file))

  def _cache_all_deps(self, view):
    time_cached = None if not("timestamp" in config.db) else config.db["timestamp"]
    for deps_file_name in config.all_dependency_files:
      config.log.debug("Caching dependencies file: {0}".format(deps_file_name))
      if time_cached == None or self._file_time(deps_file_name) > time_cached:
        self._parse_deps_file(view, deps_file_name)
      else:
        self._check_dependency_files_timestamps(deps_file_name)

  def _parse_deps_file(self, view, deps_file_name):
    config.log.debug("Parsing the full dependencies file: {0}".format(deps_file_name))
    deps_files = []
    with open(deps_file_name, "r") as file:
      for line in file:
        js_file = self._parse_deps_file_line(view, line, deps_files)
        if js_file:
          deps_files.append(js_file)
    config.db["deps_files"][deps_file_name] = deps_files
    tree_builder.add_all_files_to_tree(deps_files)

  def _check_dependency_files_timestamps(self, deps_file_name):
    deps_files = config.db["deps_files"][deps_file_name]
    now = time.localtime()
    for js_file in deps_files:
      file_details = config.db["dependencies"][js_file]
      _file_time = self.gmt__file_time(js_file)
      cached_time = file_details["timestamp"]
      if cached_time >= _file_time:
        continue
      file_details["timestamp"] = now
      tree_builder.add_file_members_to_tree(file_details["namespaces_provided"], file_details["js_file"])

  def _parse_deps_file_line(self, view, line, deps_files):
    match = parse_deps_regex.match(line)
    if not(match):
      return None

    basejs_file = view.settings().get("basejs_file")
    roots = view.settings().get("roots")
    js_file = tree_builder.get_real_path_for_file(basejs_file, roots, match.group(1))
    if js_file == None:
      return None

    namespaces_provided = match.group(2).replace("'", "").replace(" ", "").split(",")
    tree_builder.add_paths_to_tree(namespaces_provided)

    namespaces_required = match.group(3).replace("'", "").replace(" ", "").split(",")
    if not(js_file in config.db["dependencies"]) or self._file_time(js_file) > config.db["dependencies"][js_file]["timestamp"]:
        config.db["dependencies"][js_file] = {
          "timestamp": time.localtime(),
          "namespaces_provided": namespaces_provided,
          "namespaces_required": namespaces_required
        }

    return js_file
