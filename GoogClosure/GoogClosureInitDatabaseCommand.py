import sublime
import sublime_plugin
import os
import pickle
import thread
import threading
import time
import config
import re

# COMPILED REGEX
parse_deps_regex = re.compile("^goog\.addDependency\('([^']+)'\, \[([^\]]+)\], \[([^\]]+)\]\);")
member1_regex = re.compile("this.([a-zA-Z0-9_]+)")
member2_regex = re.compile("(^[a-zA-Z0-9_.]*\.|^)([a-zA-Z0-9_]+) ")


# Globals
class GoogClosureInitDatabaseCommand(sublime_plugin.EventListener):

  def on_load(self, view):
    self.init_database(view)

  def init_database(self, view):
    if config.initialising or config.db != None:
      config.log.info("Already initialised")
      return
    a_lock = thread.allocate_lock()
    with a_lock:
      if config.initialising:
        config.log.info("Already initialised")
        return
      config.initialising = True

    self.validate_settings(view)
    bg_thread = threading.Thread(target=self.background_init_database, args=[view])
    bg_thread.start()

  def validate_settings(self, view):
    for setting in config.SETTINGS:
      if not (view.settings().get(setting)):
        raise Exception("Could not find the setting [{0}] in the settings files.".format(setting))
    config.log.info("All settings validated.")

  def background_init_database(self, view):
    config.log.info("Initialising Google Closure Caches")
    sublime.set_timeout(lambda: view.set_status("googclosure", "Initialising Google Closure Caches"), 0)
    self.background_init_database_impl(view)
    config.log.info("Initialising Google Closure Caches - Done")
    sublime.set_timeout(lambda: view.erase_status("googclosure"), 0)

  def background_init_database_impl(self, view):
    basejs_file = view.settings().get("basejs_file")
    goog_deps = os.path.normpath(os.path.join(os.path.dirname(basejs_file), "deps.js"))
    config.all_dependency_files = view.settings().get("deps_paths")
    config.all_dependency_files.insert(0, goog_deps)

    if os.path.exists("goog_closure_autocomplete.db"):
      with open("goog_closure_autocomplete.db", "r") as file:
        config.db = pickle.load(file)

    config.log.info("Initialising the google closure auto-comlete database.")
    config.db = {
      "dependencies": {},
      "deps_files": {},
      "deps_tree": {}
    }

    self.cache_all_deps()

    config.db["timestamp"] = time.localtime()
    self.dump_caches()

  def dump_caches(self):
    with open("goog_closure_autocomplete.db", "wb") as file:
      pickle.dump(config.db, file)

  def file_time(self, file):
    return time.localtime(os.path.getmtime(file))

  def cache_all_deps(self, view):
    time_cached = None if not("timestamp" in config.db) else config.db["timestamp"]
    for deps_file_name in config.all_dependency_files:
      if time_cached == None or self.file_time(deps_file_name) > time_cached:
        self.parse_deps_file(view, deps_file_name)
      else:
        self.check_dependencies_timestamps(deps_file_name)

  def check_dependencies_timestamps(self, deps_file_name):
    deps_files = config.db["deps_files"][deps_file_name]
    now = time.localtime()
    for js_file in deps_files:
      file_details = config.db["dependencies"][js_file]
      file_time = self.gmt_file_time(js_file)
      cached_time = file_details["timestamp"]
      if cached_time >= file_time:
        continue
      file_details["timestamp"] = now
      self.add_file_members_to_tree(file_details["namespaces_provided"], file_details["js_file"])

  def parse_deps_file(self, view, deps_file_name):
    deps_files = []
    with open(deps_file_name, "r") as file:
      for line in file:
        js_file = self.parse_deps_file_line(view, line, deps_files)
        if js_file:
          deps_files.append(js_file)
    config.db["deps_files"][deps_file_name] = deps_files
    self.add_all_files_to_tree(view, deps_files)

  def parse_deps_file_line(self, view, line, deps_files):
    match = parse_deps_regex.match(line)
    if not(match):
      return None
    js_file = self.get_real_path_for_file(view, match.group(1))
    if js_file == None:
      return None

    namespaces_provided = match.group(2).replace("'", "").replace(" ", "").split(",")
    self.add_paths_to_tree(namespaces_provided)

    namespaces_required = match.group(3).replace("'", "").replace(" ", "").split(",")
    if not(js_file in config.db["dependencies"]) or self.file_time(js_file) > config.db["dependencies"][js_file]["timestamp"]:
        config.db["dependencies"][js_file] = {
          "timestamp": time.localtime(),
          "namespaces_provided": namespaces_provided,
          "namespaces_required": namespaces_required
        }

    return js_file

  def add_all_files_to_tree(self, view, files):
    for js_file in files:
      namespaces_provided = config.db["dependencies"][js_file]["namespaces_provided"]
      self.add_file_members_to_tree(namespaces_provided, js_file)

  def get_real_path_for_file(self, view, file):
    if file.find("..") < 0:
      abs_file = os.path.normpath(view.settings().get("basejs_file").replace("base.js", file))
      if os.path.exists(abs_file):
        return abs_file
    else:
      for root in view.settings().get("roots"):
        if file.startswith(root[1]):
          file = file[len(root[1]):]
          abs_file = os.path.normpath(os.path.join(root[0], file))
          if os.path.exists(abs_file):
            return abs_file
    return None

  def add_paths_to_tree(self, namespaces_provided):
    for ns in namespaces_provided:
      self.add_node_to_tree(ns)

  def add_file_members_to_tree(self, namespaces_provided, file):
    curr_namespace = ""
    with open(file, "r") as file_stream:
      for line in file_stream:
        matching_namespaces = filter(lambda ns: line.find(ns) >= 0, namespaces_provided)
        if (curr_namespace == "" and len(matching_namespaces) == 0):
          continue
        if (len(matching_namespaces) > 1):
          matching_namespaces.sort(lambda x, y: cmp(len(y), len(x)))
        if (len(matching_namespaces) > 0):
          curr_namespace = matching_namespaces[0]
        if (len(curr_namespace) == 0):
          continue

        match1 = member1_regex.search(line)
        match2 = member2_regex.match(line)
        if (match1):
          self.add_node_to_tree(curr_namespace + "." + match1.group(1))
        if (match2):
          self.add_node_to_tree(curr_namespace + "." + match2.group(2))

  def add_node_to_tree(self, node):
    if node.endswith("_"):  # Ignore private members
      return

    path = node.split(".")
    current_node = config.db["deps_tree"]
    for step in path:
      if not (step in current_node):
        current_node[step] = {}
      current_node = current_node[step]
