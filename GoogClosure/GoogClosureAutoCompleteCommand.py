import sublime
import sublime_plugin
import re
import logging
import os
import pickle
import thread
import threading
import time

# Globals
goog_closure_database = None
initialising = False
log = logging.getLogger("googclosure")
log.setLevel(logging.DEBUG)

# REGEX
parse_deps_regex = re.compile("^goog\.addDependency\('([^']+)'\, \[([^\]]+)\], \[([^\]]+)\]\);")
namespace_regex = re.compile("(^.*[^a-zA-Z0-9_.]|^)([a-zA-Z0-9_.]+)$")
member1_regex = re.compile("this.([a-zA-Z0-9_]+)")
member2_regex = re.compile("(^[a-zA-Z0-9_.]*\.|^)([a-zA-Z0-9_]+) ")

# TODO: Move to plugin settings file
settings = {
  "basejs_file": r"U:\shared\lib\closure-library\closure\goog\base.js",
  "deps_paths": [r"J:\dev\projects\accc\PicNet.Accc.Mvc\resources\scripts\src\deps.js"],
  "roots": [
    (r"J:\dev\projects\accc\PicNet.Accc.Mvc\resources\scripts\src\pn.accc", "../../../../accc/resources/scripts/src/pn.accc/"),
    (r"U:\shared\lib\picnet_closure_repo\src\pn", "../../../../../../../shared/picnet_closure_repo/src/pn/"),
    (r"U:\shared\lib\tablefilter\src\pn\ui\filter", "../../../../../../../shared/tablefilter/src/pn/ui/filter/"),
    (r"U:\shared\lib\closure-templates", "../../../../../../../shared/closure-templates/")
  ]
}

TESTING = True


# Classes
class GoogClosureAutoCompleteCommand(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    if goog_closure_database == None:
      return
    file = view.file_name()
    if not(file in goog_closure_database["deps"]):
      return
    namespaces_provided = goog_closure_database["deps"][file]
    self.add_file_members_to_tree(namespaces_provided, file)

  def on_query_completions(self, view, prefix, locations):
    if goog_closure_database == None:
      if TESTING:
        GoogClosureInitDatabaseCommand().on_load(view)
      else:
        log.info("completion ignored as database is not initialised")
        return

    compl_default = [view.extract_completions(prefix)]
    compl_default = [(item + "\tDefault", item) for sublist in compl_default
       for item in sublist if len(item) > 3]
    compl_default = list(set(compl_default))

    path = self.get_path_for_completion(view, prefix, locations)
    if not(path):
      return []

    raw_completions = self.get_completions_from_path(path)
    raw_completions.sort()
    completions = [(x, x) for x in raw_completions]
    completions.extend(compl_default)
    return (completions, sublime.INHIBIT_WORD_COMPLETIONS |
      sublime.INHIBIT_EXPLICIT_COMPLETIONS)

  def get_path_for_completion(self, view, prefix, locations):
    line_region = view.line(sublime.Region(locations[0]))
    line = str(view.substr(line_region))[:locations[0] - line_region.a]
    match = namespace_regex.match(line)
    if match:
      path = filter(lambda step: len(step) > 0, match.group(2).split("."))
      return path
    else:
      return None

  def get_completions_from_path(self, path):
    if not(path) or not(goog_closure_database):
      return []

    root = goog_closure_database["deps_tree"]
    node = root
    for step in path:
      if not (step in node):
        log.debug("Could not find step: [{0}] in node.".format(step))
        return self.get_partial_matches_from_node(step, node)
      else:
        node = node[step]

    if node == root:
      return []

    completions = node.keys()
    print("auto_complete - completions: {0}".format(completions))
    return completions

  def get_partial_matches_from_node(self, step, node):
    if not(step):
      return []
    completions = node.keys()
    completions = filter(lambda c: c.startswith(step), completions)
    return completions


class GoogClosureInitDatabaseCommand(sublime_plugin.EventListener):
  def on_load(self, view):
    self.init_database(view)

  def init_database(self, view):
    global goog_closure_database
    global initialising
    if initialising or goog_closure_database != None:
      return
    a_lock = thread.allocate_lock()
    with a_lock:
      if initialising:
        return
      initialising = True

    bg_thread = threading.Thread(target=self.background_init_database, args=[view])
    bg_thread.start()

  def background_init_database(self, view):
    sublime.set_timeout(lambda: view.set_status("googclosure", "Initialising Google Closure Caches"), 1)
    self.background_init_database_impl(view)
    sublime.set_timeout(lambda: view.erase_status("googclosure"), 1)

  def background_init_database_impl(self, view):
    basejs_file = settings["basejs_file"]
    goog_deps = os.path.normpath(os.path.join(os.path.dirname(basejs_file), "deps.js"))
    settings["deps_paths"].insert(0, goog_deps)

    global goog_closure_database
    if os.path.exists("goog_closure_autocomplete.db"):
      with open("goog_closure_autocomplete.db", "r") as file:
        goog_closure_database = pickle.load(file)
      if not(self.are_deps_files_expired()) and self.check_cache_timestamps():
        return
      log.info("Dependencies files expired, reloading all caches")

    log.info("Initialising the google closure auto-comlete database.")
    goog_closure_database = {"deps": {}, "deps_tree": {}, "timestamp": time.localtime()}
    print 'goog_closure_database', goog_closure_database
    self.cache_all_deps()
    self.dump_caches()

  def dump_caches(self):
    with open("goog_closure_autocomplete.db", "wb") as file:
      pickle.dump(goog_closure_database, file)

  def are_deps_files_expired(self):
    cached_time = goog_closure_database["timestamp"]
    for deps_file in settings["deps_paths"]:
      file_time = self.gmt_file_time(deps_file)
      if file_time > cached_time:
        return True
    return False

  def check_cache_timestamps(self):
    deps = goog_closure_database["deps"]
    now = time.localtime()
    dirty = False
    for js_file in deps:
      file_details = deps[js_file]
      file_time = self.gmt_file_time(js_file)
      cached_time = file_details["timestamp"]
      if cached_time >= file_time:
        continue
      dirty = True
      file_details["timestamp"] = now
      self.add_file_members_to_tree(file_details["namespaces_provided"], file_details["js_file"])
    if dirty:
      self.dump_caches()

  def gmt_file_time(self, file):
    return time.localtime(os.path.getmtime(file))

  def cache_all_deps(self):
    for deps_file in settings["deps_paths"]:
      self.parse_deps(deps_file)

  def parse_deps(self, deps_file):
    log.info("parsing: {0}".format(deps_file))
    with open(deps_file, "r") as file:
      for line in file:
        self.parse_deps_line(line)

  def parse_deps_line(self, line):
    match = parse_deps_regex.match(line)
    if not(match):
      return
    js_file = self.get_real_path_for_file(match.group(1))
    if js_file == None:
      return

    namespaces_provided = match.group(2).replace("'", "").replace(" ", "").split(",")
    namespaces_required = match.group(3).replace("'", "").replace(" ", "").split(",")
    goog_closure_database["deps"][js_file] = {"timestamp": time.localtime(), "namespaces_provided": namespaces_provided, "namespaces_required": namespaces_required}
    self.add_paths_to_tree(namespaces_provided)
    self.add_file_members_to_tree(namespaces_provided, js_file)

  def get_real_path_for_file(self, file):
    if file.find("..") < 0:
      abs_file = os.path.normpath(settings["basejs_file"].replace("base.js", file))
      if os.path.exists(abs_file):
        return abs_file
    else:
      for root in settings["roots"]:
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
    current_node = goog_closure_database["deps_tree"]
    for step in path:
      if not (step in current_node):
        current_node[step] = {}
      current_node = current_node[step]
