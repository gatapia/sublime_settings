import unittest
import jsdoc_parser
import cached_file_parser


class TestCachedFileParser(unittest.TestCase):

  def setUp(self):
    self.dependencies = {
      "tests/js/child.js": {"namespaces_provided": ["namespace.child"]},
      "tests/js/parent.js": {"namespaces_provided": ["namespace.parent"]}
    }
    self.cfp = cached_file_parser.CachedFileParser(self.dependencies, {})

  ##################
  # get_file_spec
  ##################
  def test_get_file_spec_with_non_matching_flie(self):
    self.assertIsNone(self.cfp.get_file_spec("no_match.js"))

  def test_get_file_spec_extends_full_hierarcy(self):
    exp = jsdoc_parser.parse_file("tests/js/child.js").members.keys()
    exp.extend(jsdoc_parser.parse_file("tests/js/parent.js").members.keys())
    exp = list(set(exp))
    self.assertEquals(exp, self.cfp.get_file_spec("tests/js/child.js").members.keys())

  def test_get_file_spec_with_no_hierarcy(self):
    exp = jsdoc_parser.parse_file("tests/js/parent.js")
    self.assertEquals(exp.members.keys(), self.cfp.get_file_spec("tests/js/parent.js").members.keys())

  ##########################
  # _get_file_from_namespace
  ##########################
  def test_get_file_from_namespace_with_no_match(self):
    self.assertIsNone(self.cfp._get_file_from_namespace("no_match.js"))

  def test_get_file_from_namespace_with_match(self):
    self.assertEquals("tests/js/child.js", self.cfp._get_file_from_namespace("namespace.child"))

  ###################
  # _extend_file_spec
  ###################
  def test_extend_file_spec_with_simple_properties(self):
    d1 = jsdoc_parser.File("name1", {"p1": jsdoc_parser.Member("p1", {}), "p2": jsdoc_parser.Member("p2", {})})
    d2 = jsdoc_parser.File("name2", {"p4": jsdoc_parser.Member("p4", {}), "p3": jsdoc_parser.Member("p3", {})})
    self.cfp._extend_file_spec(d1, d2)
    exp = jsdoc_parser.File("name1", {
      "p1": jsdoc_parser.Member("p1", []), "p2": jsdoc_parser.Member("p2", []),
      "p3": jsdoc_parser.Member("p3", []), "p4": jsdoc_parser.Member("p4", [])
    })
    self.assertEquals(exp.members.keys(), d2.members.keys())

  def test_extend_file_spec_with_overlapping_properties(self):
    d1 = jsdoc_parser.File("name1", {"p1": jsdoc_parser.Member("p1", {}), "p2": jsdoc_parser.Member("p2", {})})
    d2 = jsdoc_parser.File("name2", {"p2": jsdoc_parser.Member("p2", {}), "p3": jsdoc_parser.Member("p3", {})})
    self.cfp._extend_file_spec(d1, d2)
    exp = jsdoc_parser.File("name1", {
      "p1": jsdoc_parser.Member("p1", []), "p2": jsdoc_parser.Member("p2", []), "p3": jsdoc_parser.Member("p3", [])
    })
    self.assertEquals(exp.members.keys(), d2.members.keys())
