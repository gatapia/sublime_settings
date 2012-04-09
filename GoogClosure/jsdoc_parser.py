import sys
import re
import os

jsdoc_parser = sys.modules[__name__]

comment_pair_re = re.compile("/\*\*(.*?)\*/[\n\s]*([a-zA-Z0-9_.]+)", re.DOTALL)
tag_split_re = re.compile("\n\s*?\*\s*?")


def parse_file(file):
  if not(os.path.exists(file)):
    return None

  with open(file) as f:
    contents = f.read()

  members = {}
  for comment_pair in comment_pair_re.finditer(contents):
    comment = comment_pair.group(1)
    name = comment_pair.group(2)
    if comment.find("@private") >= 0:
      continue

    tags = {}
    for tag in tag_split_re.sub('\n', comment).split('@'):
      tag = tag.strip()
      if not(tag):
        continue
      idx = tag.find(' ')
      tag_name = tag if idx < 0 else tag[:idx]
      tag_doc = "" if idx < 0 else tag[idx + 1:]
      tags[tag_name] = Tag(tag_name, tag_doc)

    members[name] = Member(name, tags)

  return File(file, members)


def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default


class File():
  def __init__(self, name, members):
    self.name = name
    self.members = members
    self.constructor = jsdoc_parser.get_first([m for m in members.values() if "constructor" in m.tags])
    self.superclass = jsdoc_parser.get_first([m for m in members.values() if "extends" in m.tags])
    if self.superclass:
      self.superclass = self.superclass.tags["extends"].doc[1:-1]

  def __str__(self):
    return "Members: name: {0} members: {1}".format(self.name, "\n".join(map(lambda t: t.__str__(), self.members)))

  def __eq__(self, other):
    if isinstance(other, File):
        return self.name == other.name and self.members == other.members
    return NotImplemented


class Member():
  def __init__(self, name, tags):
    self.name = name
    self.tags = tags

  def __eq__(self, other):
    if isinstance(other, Member):
        return self.name == other.name and self.tags == other.tags
    return NotImplemented


class Tag():
  def __init__(self, name, doc):
    self.name = name
    self.doc = doc

  def __eq__(self, other):
    if isinstance(other, Tag):
        return self.name == other.name and self.doc == other.doc
    return NotImplemented
