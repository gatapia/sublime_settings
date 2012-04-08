import unittest
import config
import auto_complete


class TestAutoComplete(unittest.TestCase):

  def setUp(self):
    config.db = {
      "deps_tree": {
        "ns1": {
          "ns11": {
            "ns111": {}
          },
          "ns12": {
            "ns121": {},
            "ns122": {}
          }
        }
      }
    }

  #################
  # get_completions
  #################
  def test_get_completions_with_no_match(self):
    self.assertEquals([], auto_complete.get_completions("nomatch"))

  def test_get_completions_with_full_match_of_single_ns(self):
    self.assertEquals(["ns11", "ns12"], auto_complete.get_completions("ns1"))

  def test_get_completions_with_full_match_of_long_ns(self):
    self.assertEquals(["ns121", "ns122"], auto_complete.get_completions("ns1.ns12"))

  def test_get_completions_with_partial_match_of_root_ns(self):
    self.assertEquals(["ns1"], auto_complete.get_completions("n"))

  def test_get_completions_with_partial_match_of_child_ns(self):
    self.assertEquals(["ns11", "ns12"], auto_complete.get_completions("ns1.ns"))

  ######################
  # _get_completion_path
  ######################
  def test_get_completion_path_with_non_valid_line(self):
    self.assertIsNone(auto_complete._get_completion_path('....'))
    self.assertIsNone(auto_complete._get_completion_path(',.,.,.,'))

  def test_get_completion_path_with_a_signle_slash_comment(self):
    self.assertEquals(["path", "is", "this"], auto_complete._get_completion_path('  // Comment path.is.this'))
    self.assertEquals(["path", "is", "this2"], auto_complete._get_completion_path('// path.is.this2'))
    self.assertEquals(["path", "is", "this3"], auto_complete._get_completion_path('//path.is.this3'))
    self.assertEquals(["path", "is", "this4"], auto_complete._get_completion_path('Some non Comment // path.is.this4'))

  def test_get_completion_path_with_a_star_comment(self):
    self.assertEquals(["path", "is", "this"], auto_complete._get_completion_path('  /* Comment path.is.this'))
    self.assertEquals(["path", "is", "this2"], auto_complete._get_completion_path('/** path.is.this2'))
    self.assertEquals(["path", "is", "this3"], auto_complete._get_completion_path('*path.is.this3'))
    self.assertEquals(["path", "is", "this4"], auto_complete._get_completion_path('** path.is.this4'))

  def test_single_ns_step_match(self):
    self.assertEquals(["this"], auto_complete._get_completion_path('  /* Comment this'))
    self.assertEquals(["this2"], auto_complete._get_completion_path('// this2'))
    self.assertEquals(["this3"], auto_complete._get_completion_path('...........this3'))
    self.assertEquals(["this4"], auto_complete._get_completion_path('       this4'))

  def test_multi_step_match(self):
    self.assertEquals(["path", "is", "this"], auto_complete._get_completion_path('........path.is.this'))
    self.assertEquals(["path", "is", "this2"], auto_complete._get_completion_path('path.is.this2'))
    self.assertEquals(["path", "is", "this3"], auto_complete._get_completion_path('     path.is.this3'))
    self.assertEquals(["path", "is", "this4"], auto_complete._get_completion_path(',,,path.is.this4'))

  ############################
  # _get_completions_from_path
  ############################

  def test_get_completions_from_path_with_full_ns_match(self):
    self.assertEquals(["ns11", "ns12"], auto_complete._get_completions_from_path(["ns1"]))
    self.assertEquals(["ns121", "ns122"], auto_complete._get_completions_from_path(["ns1", "ns12"]))

  def test_get_completions_from_path_with_no_match(self):
    self.assertEquals([], auto_complete._get_completions_from_path(["ns3"]))

  ################################
  # _get_partial_matches_from_node
  ################################
  def test_get_partial_matches_from_node_with_no_step(self):
    self.assertEquals([], auto_complete._get_partial_matches_from_node("", {}))

  def test_get_partial_matches_from_node_with_single_match(self):
    self.assertEquals(["ns2"], auto_complete._get_partial_matches_from_node("ns", {"1": {}, "ns2": {}, "3": {}}))

  def test_get_partial_matches_from_node_with_multiple_matches(self):
    self.assertEquals(["ns2", "ns3"], auto_complete._get_partial_matches_from_node("ns", {"1": {}, "ns2": {}, "ns3": {}}))
