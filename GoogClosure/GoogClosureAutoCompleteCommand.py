import sublime
import sublime_plugin
import config
import auto_complete
import tree_builder


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
    default_completions = [(item + "\tDefault", item) for sublist in [view.extract_completions(prefix)]
     for item in sublist if len(item) > 3]
    default_completions = list(set(default_completions))

    line_region = view.line(sublime.Region(locations[0]))
    line = str(view.substr(line_region))[:locations[0] - line_region.a]

    completions = [(x, x) for x in auto_complete.get_completions(line)]
    completions.extend(default_completions)
    return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
