import sublime
import sublime_plugin
import re
import logging
import os

# Globals
goog_closure_database = None
log = logging.getLogger('googclosure')
log.setLevel(logging.DEBUG)
parse_deps_regex = re.compile('^goog\.addDependency\(\'([^\']+)\'\, \[([^\]]+)\], \[([^\]]+)\]\);')
namespace_regex = re.compile('(^.*[^a-zA-Z0-9_.]|^)([a-zA-Z0-9_.]+)$')
TESTING = True


# Classes
class GoogClosureAutoCompleteCommand(sublime_plugin.EventListener):
  def on_query_completions(self, view, prefix, locations):
    if goog_closure_database == None:
      if TESTING:
        GoogClosureInitDatabaseCommand().on_load(None)
      else:
        log.info("completion ignored as database is not initialised")
        return

    path = self.get_path_for_completion(view, prefix, locations)
    completions = [(x, x) for x in self.get_completions_from_path(path)]
    return completions

  def get_path_for_completion(self, view, prefix, locations):
    line_region = view.line(sublime.Region(locations[0]))
    line = str(view.substr(line_region))[:locations[0] - line_region.a]
    match = namespace_regex.match(line)
    if match:
      path = filter(lambda step: len(step) > 0, match.group(2).split('.'))
      return path
    else:
      return None

  def get_completions_from_path(self, path):
    if not(path):
      return []

    root = goog_closure_database['deps_tree']
    node = root
    for step in path:
      if not (step in node):
        log.debug('Could not find step: [{0}] in node.'.format(step))
        return self.get_partial_matches_from_node(step, node)
      else:
        node = node[step]

    if node == root:
      return []

    completions = node.keys()
    completions.sort()
    print('auto_complete - completions: {0}'.format(completions))
    return completions

  def get_partial_matches_from_node(self, step, node):
    if not(step):
      return []
    completions = node.keys()
    completions = filter(lambda c: c.startswith(step), completions)
    completions.sort()

    print('auto_complete (partial) - completions: {0}'.format(completions))
    return completions


class GoogClosureInitDatabaseCommand(sublime_plugin.EventListener):
  def on_load(self, view):
    base_file = 'U:\\shared\\lib\\closure-library\\closure\\goog\\base.js'
    deps_paths = ['J:\\dev\\projects\\accc\\PicNet.Accc.Mvc\\resources\\scripts\\src\\deps.js']
    self.init_database(base_file, deps_paths)

  def init_database(self, base_file, deps_paths):
    global goog_closure_database
    if (goog_closure_database != None):
      return
    log.info('Initialising the google closure auto-comlete database.')
    goog_closure_database = {'parsed_deps_files': [], 'deps': {}, 'deps_tree': {}}

    goog_deps = os.path.join(os.path.dirname(base_file), 'deps.js')
    deps_paths.insert(0, goog_deps)
    self.cache_all_deps(deps_paths)

  def cache_all_deps(self, deps_paths):
    for deps_file in deps_paths:
      self.parse_deps(deps_file)

  def parse_deps(self, deps_file):
    if (deps_file in goog_closure_database['parsed_deps_files']):
      return
    goog_closure_database['parsed_deps_files'].append(deps_file)

    log.info('parsing: {0}'.format(deps_file))
    with open(deps_file, 'r') as file:
      for line in file:
        self.parse_deps_line(line)

  def parse_deps_line(self, line):
    match = parse_deps_regex.match(line)
    if not(match):
      return
    js_file = match.group(1)
    namespaces_provided = match.group(2).replace('\'', '').replace(' ', '').split(',')
    namespaces_required = match.group(3).replace('\'', '').replace(' ', '').split(',')
    goog_closure_database['deps'][js_file] = {'namespaces_provided': namespaces_provided, 'namespaces_required': namespaces_required}
    self.expand_tree(namespaces_provided)
    log.debug("File: {0} provided: {1} required: {2}", js_file, namespaces_provided, namespaces_required)

  def expand_tree(self, namespaces_provided):
    for ns in namespaces_provided:
      self.add_node_to_tree(ns)

  def add_node_to_tree(self, node):
    path = node.split('.')
    current_node = goog_closure_database['deps_tree']
    for step in path:
      if not (step in current_node):
        current_node[step] = {}
      current_node = current_node[step]
