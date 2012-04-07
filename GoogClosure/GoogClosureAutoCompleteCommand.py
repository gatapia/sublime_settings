import sublime
import sublime_plugin
import config
import GoogClosureInitDatabaseCommand
import re
import tree_builder

# COMPILED REGEX
namespace_regex = re.compile("(^.*[^a-zA-Z0-9_.]|^)([a-zA-Z0-9_.]+)$")


# Classes
class GoogClosureAutoCompleteCommand(sublime_plugin.EventListener):

  def on_pre_save(self, view):
    if config.db == None:
      # TODO: Consider adding this to a queue to be reprocessed once the DB init is done.
      config.log.debug("Database is not initialised so ignoring this save event.")
      return

    file = view.file_name()
    if not(file in config.db["dependencies"]):
      config.log.debug("File saved is not in the dependencies map, ignoring.")
      return

    namespaces_provided = config.db["dependencies"][file]
    tree_builder.add_file_members_to_tree(namespaces_provided, file)

  def on_query_completions(self, view, prefix, locations):
    config.log.debug("on_query_completions prefix: {0}".format(prefix))

    if config.db == None:
      if config.TESTING:
        config.log.debug("In TESTING - creating database (This would not happen in prod).")
        GoogClosureInitDatabaseCommand.GoogClosureInitDatabaseCommand().on_load(view)

      config.log.info("Completion ignored as database is not initialised")
      return []

    compl_default = [view.extract_completions(prefix)]
    compl_default = [(item + "\tDefault", item) for sublist in compl_default
       for item in sublist if len(item) > 3]
    compl_default = list(set(compl_default))

    path = self._get_path_for_completion(view, prefix, locations)
    if not(path):
      return []

    raw_completions = self._get_completions_from_path(path)
    raw_completions.sort()

    config.log.info("auto_complete - path: {0} default: {1} completions: {2}".format(path, compl_default, raw_completions))

    completions = [(x, x) for x in raw_completions]
    completions.extend(compl_default)
    return (completions, sublime.INHIBIT_WORD_COMPLETIONS |
      sublime.INHIBIT_EXPLICIT_COMPLETIONS)

  def _get_path_for_completion(self, view, prefix, locations):
    line_region = view.line(sublime.Region(locations[0]))
    line = str(view.substr(line_region))[:locations[0] - line_region.a]
    match = namespace_regex.match(line)
    if match:
      return filter(lambda step: len(step) > 0, match.group(2).split("."))
    else:
      return None

  def _get_completions_from_path(self, path):
    if not(path) or not(config.db):
      return []

    node = config.db["deps_tree"]
    for step in path:
      if not (step in node):
        config.log.debug("_get_completions_from_path - path: {0} could not be found.  Looking for partial matches from node: {1}".format(path, node))
        return self._get_partial_matches_from_node(step, node)
      else:
        node = node[step]

    if node == config.db["deps_tree"]:
      return []

    completions = node.keys()
    return completions

  def _get_partial_matches_from_node(self, step, node):
    if not(step):
      return []
    completions = node.keys()
    completions = filter(lambda c: c.startswith(step), completions)
    return completions
