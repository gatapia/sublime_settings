import jsdoc_parser
import os


class CachedFileParser():

  def __init__(self, dependencies, cache):
    self.dependencies = dependencies
    self.cache = cache

  def get_file_spec(self, file):
    if file in self.cache:
      return self.cache[file]

    if not(os.path.exists(file)):
      return None

    self.cache[file] = self._deep_parse_file(file)
    return self.cache[file]

  def _deep_parse_file(self, file):
    file_spec = jsdoc_parser.parse_file(file)
    self._append_super_class_file_spec(file_spec)
    return file_spec

  def _append_super_class_file_spec(self, file_spec):
    if not(file_spec.superclass):
      return file_spec

    file = self._get_file_from_namespace(file_spec.superclass)
    super_class_file_spec = self.get_file_spec(file)
    self._extend_file_spec(super_class_file_spec, file_spec)
    # TODO: Add the default object members here also.

  def _get_file_from_namespace(self, namespace):
    for file_name in self.dependencies:
      deps = self.dependencies[file_name]
      if namespace in deps["namespaces_provided"]:
        return file_name

  def _extend_file_spec(self, source, target):
    for member in source.members:
      target.members[member] = source.members[member]
