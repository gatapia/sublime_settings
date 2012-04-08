import config
import sys
import re

auto_complete = sys.modules[__name__]

namespace_regex = re.compile("(^.*[^a-zA-Z0-9_.]|^)([a-zA-Z0-9_.]+)$")


def get_completions(line):
  config.log.debug("on_query_completions line: {0}".format(line))

  if config.db == None:
    config.log.info("Completion ignored as database is not initialised")
    return []

  line = _get_completion_path(line)
  if not(line):
    return []

  completions = auto_complete._get_completions_from_path(line)

  config.log.info("auto_complete - line: {0} completions: {1}".format(line, completions))
  return completions


def _get_completion_path(line):
  match = namespace_regex.match(line)
  if match:
    path = filter(lambda step: len(step) > 0, match.group(2).split("."))
    if not (path):
      return None
    return path
  else:
    return None


def _get_completions_from_path(path):
  if not(path) or not(config.db):
    return []

  node = config.db["deps_tree"]
  for step in path:
    if not (step in node):
      config.log.debug("_get_completions_from_path - path: {0} could not be found.  Looking for partial matches from node: {1}".format(path, node))
      return auto_complete._get_partial_matches_from_node(step, node)
    else:
      node = node[step]

  if node == config.db["deps_tree"]:
    return []

  completions = node.keys()
  completions.sort()
  return completions


def _get_partial_matches_from_node(step, node):
  if not(step):
    return []
  completions = node.keys()
  completions = filter(lambda c: c.startswith(step), completions)
  completions.sort()
  return completions
