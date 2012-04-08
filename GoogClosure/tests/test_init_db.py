import unittest
import config
import init_db


class TestInitDB(unittest.TestCase):

  def setUp(self):
    config.db = {
      "dependencies": {},
      "deps_tree": {}
    }

  ###############
  # validate_path
  ###############

  def test_validate_path_succeeds_if_path_exists(self):
    init_db.validate_path("init_db.py")

  def test_validate_path_fails_with_invalid_path(self):
    try:
      init_db.validate_path("missing_file.ext")
      self.fail("Sould have failed")
    except:
      pass

  ######################
  # parse_deps_file_line
  ######################

  def test_parse_deps_file_line_read_if_valid(self):
    line = "goog.addDependency('../relative/file.js', ['prov_ns1', 'prov_ns2'], ['req_ns1']);"
    init_db._parse_deps_file_line("/path/base.js", [["\\absolute\\path", "../relative/file.js"]], line, False)
    namespaces_provided = ["prov_ns1", "prov_ns2"]
    namespaces_required = ["req_ns1"]
    actual = config.db["dependencies"]["\\absolute\\path"]
    self.assertEqual(namespaces_provided, actual["namespaces_provided"])
    self.assertEqual(namespaces_required, actual["namespaces_required"])
    self.assertEqual({"prov_ns1": {}, "prov_ns2": {}}, config.db["deps_tree"])

  def test_parse_deps_file_line_ignored_if_not_valid_line(self):
    line = "goog.addDependency('../relative/file.js', ['prov_ns1', 'prov_ns2'], ['req_ns1']);"
    init_db._parse_deps_file_line("/path/base.js", [["\\absolute\\path", "../unknownpath/file.js"]], line, False)
    self.assertEqual({}, config.db["dependencies"])
    self.assertEqual({}, config.db["deps_tree"])
