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
member1_regex = re.compile('this.([a-zA-Z0-9_]+)')
member2_regex = re.compile('(^[a-zA-Z0-9_.]*\.|^)([a-zA-Z0-9_]+) ')
settings = {}
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
    global settings
    settings['basejs_file'] = 'U:\\shared\\lib\\closure-library\\closure\\goog\\base.js'
    settings['deps_paths'] = ['J:\\dev\\projects\\accc\\PicNet.Accc.Mvc\\resources\\scripts\\src\\deps.js']
    settings['roots'] = [
      ("J:\\dev\\projects\\accc\\PicNet.Accc.Mvc\\resources\\scripts\\src\\pn.accc\\", "../../../../accc/resources/scripts/src/pn.accc/"),
      ("U:\\shared\\lib\\picnet_closure_repo\\src\\pn", "../../../../../../../shared/picnet_closure_repo/src/pn/"),
      ("U:\\shared\\lib\\tablefilter\\src\\pn\\ui\\filter", "../../../../../../../shared/tablefilter/src/pn/ui/filter/"),
      ("U:\\shared\\lib\\closure-templates", "../../../../../../../shared/closure-templates/")  
    ]
    self.init_database()

  def init_database(self):
    global goog_closure_database
    if (goog_closure_database != None):
      return
    log.info('Initialising the google closure auto-comlete database.')
    goog_closure_database = {'parsed_deps_files': [], 'deps': {}, 'deps_tree': {}}

    basejs_file = settings['basejs_file']
    goog_deps = os.path.join(os.path.dirname(basejs_file), 'deps.js')
    settings['deps_paths'].insert(0, goog_deps)
    self.cache_all_deps()

  def cache_all_deps(self):
    for deps_file in settings['deps_paths']:
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
    self.add_paths_to_tree(namespaces_provided)
    self.add_file_members_to_tree(namespaces_provided, js_file)
    log.debug("File: {0} provided: {1} required: {2}", js_file, namespaces_provided, namespaces_required)

  def add_paths_to_tree(self, namespaces_provided):
    for ns in namespaces_provided:
      self.add_node_to_tree(ns)

  def add_file_members_to_tree(self, namespaces_provided, file):
    for root in settings['roots']:
      if file.startswith(root[1]):
        file = file[len(root[1]):]
        abs_file = os.path.join(root[0], file)
        if not (os.path.exists(abs_file)):
          print 'could not find file:', abs_file
          return
        self.add_file_members_to_tree_impl(namespaces_provided, abs_file)

  def add_file_members_to_tree_impl(self, namespaces_provided, file):
    curr_namespace = ''
    with open(file, 'r') as file_stream:
      for line in file_stream:
        matching_namespaces = filter(lambda ns: line.find(ns) >= 0, namespaces_provided)
        if (curr_namespace == '' and len(matching_namespaces) == 0):
          continue
        if (len(matching_namespaces) > 1):
          matching_namespaces.sort(lambda x, y: cmp(len(y), len(x)))
        if (len(matching_namespaces) > 0):
          curr_namespace = matching_namespaces[0]
        if (len(curr_namespace) == 0):
          continue

        match1 = member1_regex.search(line)
        match2 = member1_regex.match(line)
        if (match1):
          self.add_node_to_tree(curr_namespace + '.' + match1.group(1))
        if (match2):
          self.add_node_to_tree(curr_namespace + '.' + match2.group(2))

  def add_node_to_tree(self, node):
    path = node.split('.')
    current_node = goog_closure_database['deps_tree']
    for step in path:
      if not (step in current_node):
        current_node[step] = {}
      current_node = current_node[step]
