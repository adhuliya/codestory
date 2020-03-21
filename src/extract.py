#!/usr/bin/env python3

"""
This module contains the logic to extract
the blocks and their information form a given string.
The given string is generally the contents of a file.
"""

import re
from typing import List, Dict

import common_util as cutil
import util as util
from os import path as osp
import os
import io
import sys

theStart = (r"{commentChars}>>\s*codestory\s+(?P<name>\w+)\.(?P<level>#*)"
            r"(?P<seq>\d+)\s+[sS][tT][aA][rR][tT]")
theEnd   = (r".*{commentChars}>>\s*codestory\s+(?P=name)"
            r"\.(?P=level)(?P=seq)\s+[eE][nN][dD]")
theBlock = theStart + r".*" + theEnd
            
aStart = r"{commentChars}>>\s*codestory\s+\w+\.#*\d+\s+[sS][tT][aA][rR][tT]"
aEnd = r"{commentChars}>>\s*codestory\s+\w+\.#*\d+\s+[eE][nN][dD]"
aStartOrEnd = r"{commentChars}>>\s*codestory\s+\w+\.#*\d+\s+([sS][tT][aA][rR][tT]|[eE][nN][dD])"

# special comment line (full line)
specialComment = r"^\s*{commentChars}>>(?P<content>.*)$"
# standard comment line (full line)
standardComment = r"^\s*{commentChars}"

# Map of the filetype and the single line commentChars characters
# FIXME: The system currently doesn't handle multiline comments.
fileCommentMap: Dict[str, str] = {
  ".cpp": "//",
  ".c": "//",
  ".h": "//",
  ".def": "//",
  ".s": ";",
  ".sh": "#",
  ".py": "#",
}

class FileInfo:
  def __init__(self,
               filePath: util.AbsFilePathT
  ) -> None:
    self.filePath = filePath
    self.mtime_ns = cutil.getFileModTimeInNanoSecs(filePath)

class Block:
  """
  This class represents a single block extracted from the text.
  """
  def __init__(self,
    name: str = "",
    level: int = 0,
    seq: int = 0, # sequence
    content: str = "",
    commentChars: str = "//",
    fileInfo: FileInfo = None,
    lineNum: int = 1,
  ) -> None:
    self.name = name
    self.level = level
    self.seq = seq
    self.content = content
    self.commentChars = commentChars
    self.fileInfo = fileInfo
    self.lineNum = lineNum

    # to be set after processing the self.content
    self.heading = ""
    self.writeup = [] # list of lines
    self.code = [] # list of lines

  def processContent(self):
    """Processes self.content and divides it sequentially into:
    1. heading (oneline)
    2. writeup (the intro paragraphs in markdown)
    3. the code that the writeup refers to
    """
    lines = self.content.splitlines()

    aStartOrEndPattern = re.compile(aStartOrEnd.format(
      commentChars=self.commentChars))
    specialCommentPattern = re.compile(
      specialComment.format(commentChars=self.commentChars))
    state = 1 # 1 = heading
    self.lineNum += 1

    for line in lines:
      if aStartOrEndPattern.search(line):
        continue # ignore start and end block indicators

      if state == 3: # in the code area
        if specialCommentPattern.search(line):
          continue # don't add special comments to code
        self.code.append(line)
        continue

      m = specialCommentPattern.search(line)
      if m and state == 1: # the heading
        self.heading = m.group("content")
        self.lineNum += 1
        state = 2
        continue
      elif m and state == 2: # the writeup
        # writeup should immediately follow the start block indicator
        self.lineNum += 1
        if m.group("content").strip():
          self.writeup.append(m.group("content"))
        else:
          self.writeup.append("\n")
        self.writeup.append("\n")
        continue

      if not m:
        state = 3 # now everything is code 
        self.code.append(line)
        continue

  def __str__(self):
    return f"{self.name}:{self.level}:{self.seq}:\n{self.content}"

  def __repr__(self): return self.__str__()

  def __lt__(self, other):
    if self.name < other.name:
      return True
    elif self.name == other.name and self.seq < other.seq:
      return True
    return False

  def __eq__(self, other):
    return self.name == other.name and self.seq == other.seq

def extractBlocksFromFile(absFilePath: util.AbsFilePathT) -> List[Block]:
  """Extracts all the blocks from the given file."""
  results = []

  ext = osp.splitext(absFilePath)[1]
  if ext in fileCommentMap:
    try:
      with open(absFilePath) as f:
        commentChars = fileCommentMap[ext]
        blocks = extractBlocks(f.read(), commentChars)
        results.extend(blocks)
    except UnicodeDecodeError as e:
      pass
    except Exception as e:
      print("CodeStory: ERROR:", e, file=sys.stderr)
      print("CodeStory: ERROR:", "File:", absFilePath, file=sys.stderr)
      raise e

  return results

def extractBlocks(s: str, commentChars: str= "//") -> List[Block]:
  """
  Extracts blocks from the given string.
  """
  aStartPattern = re.compile(aStart.format(commentChars=commentChars))
  blockPattern = re.compile(theBlock.format(commentChars=commentChars), re.DOTALL)

  results = []
  startPos = 0
  while True:
    match = blockPattern.search(s, pos=startPos)
    if match:
      b = Block(
            name=match.group("name"),
            level=len(match.group("level")),
            seq=int(match.group("seq")),
            content=match.group(),
            commentChars=commentChars,
          )
      # this is the line number of the //>>BLOCK(... pattern
      b.lineNum = cutil.calcLineNum(s, match.start())
      print(b.lineNum, b.name, b.seq) #delit
      results.append(b)

      # check if another block starts inside this block
      # skip 10 chars otherwise it will match this block
      nested = aStartPattern.search(match.group(), pos=10)
      if nested:
        startPos = match.start() + 10
      else:
        startPos = match.end() # start searching for the next
    else:
      break

  return results

def makeMarkdown(blocks: List[Block]) -> List[io.StringIO]:
  blocks.sort()

  # a tuple of (name, heading) used for docIndex
  namesAndHeadings = []
  docDetails = io.StringIO()

  baseLevel = 2  # i.e. start from h2
  currName = ""  # current name of the block

  for block in blocks:
    firstBlock = False
    if currName != block.name:
      firstBlock = True
      currName = block.name
      namesAndHeadings.append((currName, block.heading))

    if firstBlock:
      docDetails.write(f"\n\n<a name='{currName}'></a>\n")
      level = "#" * (block.level + baseLevel)
    else:
      level = "#" * (block.level + baseLevel + 1)

    docDetails.write(f"{level} {block.heading}\n")

    docDetails.writelines(block.writeup)

    sourceFileName = osp.basename(block.fileInfo.filePath)
    docDetails.write(f"\n\n[{sourceFileName}](file://{block.fileInfo.filePath})\n\n")

    docDetails.write(f"<pre class='language-cpp line-numbers'"
                     f" data-start='{block.lineNum}'>"
                     f"<code>\n")
    for codeLine in block.code:
      space = " " * 4
      docDetails.write(f"{space}{codeLine}\n")
    docDetails.write(f"</code></pre>\n")

  docIndex = io.StringIO()

  docIndex.write("\n\n# Index\n")
  for name, heading in namesAndHeadings:
    docIndex.write(f"\n1. [{heading}](#{name})") 

  return [docIndex, docDetails]

def printMarkdown(content: List[io.StringIO],
                  handle: io.TextIOBase):
  map(lambda x: handle.write(x.getvalue()), content)

#  docHeading = io.StringIO()
#  docHeading.write("# Clang/LLVM Notes\n")
#  docHeading.write("These are automatically generated notes from the")
#  docHeading.write(" source code of Clang/LLVM 8.0.1.")
#  docHeading.write("\n\n") # para change
#  docHeading.write("**FIXME** and **TODO** signify some remaining work")
#
#  docFooter = io.StringIO()
#  docFooter.write("<br><br><br>\n")
#  docFooter.write("<div class='footer'> <br/> &copy; LEG Team <br/> </div>\n")

