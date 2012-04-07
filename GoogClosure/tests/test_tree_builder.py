import unittest
import tree_builder
import config


class TestTreeBuilder(unittest.TestCase):

  def setUp(self):
    config.db = {
      "deps_tree": {},
      "dependencies": {
        "tests/dummy.js": {
          "namespaces_provided": ["namespace.dummy1", "namespace.dummy2"]
        }
      }
    }

  #############################
  # add_all_files_to_tree tests
  #############################
  def test_add_all_files_to_tree_for_single_file(self):
    tree_builder.add_all_files_to_tree(["tests/dummy.js"])
    self.assertEqual({"namespace": {
      "dummy1": {"prop1": {}, "prop2": {}, "func1": {}, "func2": {}},
      "dummy2": {"prop3": {}, "prop4": {}, "func3": {}, "func4": {}},
    }}, config.db["deps_tree"])

  ##############################
  # get_real_path_for_file tests
  ##############################
  def test_get_real_path_for_file_for_goog_file(self):
    actual = tree_builder.get_real_path_for_file(r"U:\shared\lib\closure-library\closure\goog\base.js", [], r"array\array.js")
    self.assertEqual(actual, r"U:\shared\lib\closure-library\closure\goog\array\array.js")

  def test_get_real_path_for_file_for_user_file(self):
    actual = tree_builder.get_real_path_for_file(r"path\base.js", [["tests\\", "..\\path2\\"]], r"..\path2\dummy.js")
    self.assertEqual(actual, r"tests\dummy.js")

  ##############################
  # add_namespaces_to_tree tests
  ##############################
  def test_add_namespaces_to_tree_get_inserted_into_deps_tree(self):
    tree_builder.add_namespaces_to_tree(["ns.ns1", "ns.ns2", "ns.ns3", "ns4"])
    self.assertEqual({"ns": {
      "ns1": {}, "ns2": {}, "ns3": {}
    }, "ns4": {}}, config.db["deps_tree"])

  ################################
  # add_file_members_to_tree tests
  ################################
  def test_add_file_members_to_tree_with_valid_test_file(self):
    tree_builder.add_file_members_to_tree(["namespace.dummy1", "namespace.dummy2"], "tests/dummy.js")
    self.assertEqual({"namespace": {
      "dummy1": {"prop1": {}, "prop2": {}, "func1": {}, "func2": {}},
      "dummy2": {"prop3": {}, "prop4": {}, "func3": {}, "func4": {}},
    }}, config.db["deps_tree"])

  #########################
  # _add_node_to_tree tests
  #########################

  def test_add_node_to_tree_with_single_step_node(self):
    tree_builder._add_node_to_tree('test_node')
    self.assertEqual({"test_node": {}}, config.db["deps_tree"])

  def test_add_node_to_tree_with_multiple_steps_node(self):
    tree_builder._add_node_to_tree('test.node')
    self.assertEqual({"test": {"node": {}}}, config.db["deps_tree"])

  def test_add_node_to_tree_with_multiple_child_nodes(self):
    tree_builder._add_node_to_tree('test.node1')
    tree_builder._add_node_to_tree('test.node2')
    self.assertEqual({"test": {"node1": {}, "node2": {}}}, config.db["deps_tree"])

  def test_add_node_to_tree_with_multiple_root_nodes(self):
    tree_builder._add_node_to_tree('test1.node')
    tree_builder._add_node_to_tree('test2.node')
    self.assertEqual({"test1": {"node": {}}, "test2": {"node": {}}}, config.db["deps_tree"])

  #####
  # run
  #####
if __name__ == '__main__':
    unittest.main()
