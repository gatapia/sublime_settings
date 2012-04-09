import unittest
import jsdoc_parser


class TestJsDocParser(unittest.TestCase):

  def setUp(self):
    pass

  ############
  # parse_file
  ############
  def test_parse_missing_file(self):
    self.assertIsNone(jsdoc_parser.parse_file("no_file.js"))

  def test_parse_simple_file(self):
    file_spec = jsdoc_parser.parse_file("tests/js/parent.js")
    self.assertEquals("tests/js/parent.js", file_spec.name)
    self.assertEquals(['namespace.parent', 'namespace.child.prototype.func3', 'namespace.child.prototype.func4', 'this.prop3', 'this.prop4'], file_spec.members.keys())
    self.assertEquals("namespace.parent", file_spec.constructor.name)
    self.assertIsNone(None, file_spec.superclass)

  def test_parse_file_with_super_class(self):
    file_spec = jsdoc_parser.parse_file("tests/js/child.js")
    self.assertEquals("tests/js/child.js", file_spec.name)
    exp_members = ['namespace.child', 'namespace.child.prototype.func1', 'namespace.child.prototype.func2', 'this.prop1', 'this.prop2']
    exp_members.sort()
    act_members = file_spec.members.keys()
    act_members.sort()
    self.assertEqual(exp_members, act_members)
    self.assertEquals("namespace.child", file_spec.constructor.name)
    self.assertEquals("namespace.parent", file_spec.superclass)
