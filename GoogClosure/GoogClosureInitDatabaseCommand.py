import sublime
import sublime_plugin
import thread
import threading
import config
import init_db

# COMPILED REGEX


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

    settings = view.settings()
    self._load_and_validate_settings(settings)

    a_lock = thread.allocate_lock()
    with a_lock:
      if config.initialising:
        config.log.debug("Database initialising. Ignoring call to init_database.")
        return
      config.initialising = True

    status = {
      "set": lambda message: sublime.set_timeout(lambda: status.set_status("googclosure", message), 0),
      "erase": lambda: sublime.set_timeout(lambda: status.erase_status("googclosure"), 0)
    }
    bg_thread = threading.Thread(target=init_db.background_init_database, args=[
      view,
      settings.get("basejs_file"),
      settings.get("roots"),
      settings.get("deps_paths")])
    bg_thread.start()

  def _load_and_validate_settings(self, settings):
    settings = sublime.load_settings('GoogClosure.sublime-settings')
    for setting in config.SETTINGS:
      if not (settings.get(setting)):
        raise Exception("Could not find the setting [{0}] in the settings files.".format(setting))
      settings.set(setting, settings.get(setting))
    init_db.validate_path(settings.get("basejs_file"))
    for path in settings.get("deps_paths"):
      init_db.validate_path(path)
    for path in settings.get("roots"):
      init_db.validate_path(path.split(' ')[0])
    config.log.debug("All settings loaded.")
