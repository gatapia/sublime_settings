import sublime
import sublime_plugin
import re


class GoogClosureAutoCompleteCommand(sublime_plugin.EventListener):
  def on_query_completions(self, view, prefix, locations):
    # start = locations[0] - len(prefix)
    # trigger_token = view.substr(sublime.Region(start, start + len(prefix)))
    return []


class GoogClosureInitDatabaseCommand(sublime_plugin.EventListener):
  def on_load(self, view):
    reload_settings(view)

    if view.is_scratch() or view.settings().get('googclosure') == False or \
      is_database_initialised(view):
        return

    init_database(view)

  def reload_settings(self, view):
    '''Restores user settings.'''
    settings = sublime.load_settings(__name__ + '.sublime-settings')
    settings.clear_on_change(__name__)
    settings.add_on_change(__name__, settings_changed)

    for setting in ALL_SETTINGS:
        if settings.get(setting) != None:
            view.settings().set(setting, settings.get(setting))

    if view.settings().get('googclosure') == None:
        view.settings().set('googclosure', True)

  def is_database_initialised(self, view):
    return false

  def init_database(self, view):
    return false
