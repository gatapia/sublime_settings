import sys
import config
import os
import re

tree_builder = sys.modules[__name__]

# COMPILED REGEX
member1_regex = re.compile("this.([a-zA-Z0-9_]+)")
member2_regex = re.compile("(^[a-zA-Z0-9_.]*\.|^)([a-zA-Z0-9_]+) ")


def add_all_files_to_tree(files):
  config.log.debug('add_all_files_to_tree #: {0}'.format(len(files)))

  for js_file in files:
    namespaces_provided = config.db["dependencies"][js_file]["namespaces_provided"]
    tree_builder.add_file_members_to_tree(namespaces_provided, js_file)


def get_real_path_for_file(basejs_file, roots, file):
  # This predicate assumes that all non 'goog' namespaces have a '..' in the path.
  # I'm not sure if this is a safe assumption, I would say it's not
  if file.find("..") < 0:
    abs_file = os.path.normpath(basejs_file.replace("base.js", file))
    if os.path.exists(abs_file):
      return abs_file
  else:
    for root in roots:
      if file.startswith(root[1]):
        file = file[len(root[1]):]
        abs_file = os.path.normpath(os.path.join(root[0], file))
        if os.path.exists(abs_file):
          return abs_file
  return None


def add_namespaces_to_tree(namespaces):
  config.log.debug("Adding namespeces to the deps tree: {0}".format(namespaces))
  for namespace in namespaces:
    tree_builder._add_node_to_tree(namespace)


def add_file_members_to_tree(namespaces_provided, file):
  curr_namespace = ""
  nodes = []
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
      node = None

      if (match1):
        node = curr_namespace + "." + match1.group(1)
      if (match2 and match2.group(1) + match2.group(2) != curr_namespace):
        node = curr_namespace + "." + match2.group(2)

      if node:
        tree_builder._add_node_to_tree(node)
        nodes.append(node)
  config.log.debug("Adding file to the deps tree: {0} - {1}".format(file, node))


def _add_node_to_tree(node):
  if node.endswith("_"):  # Ignore private members
    return

  path = node.split(".")
  current_node = config.db["deps_tree"]
  for step in path:
    if not (step in current_node):
      current_node[step] = {}
    current_node = current_node[step]
