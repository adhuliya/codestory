#!/usr/bin/env python3
import re
from typing import List, Dict

import common_util as util
from os import path as osp
import os
import io
import sys

theStart = r"{comment}>>\s*BLOCK\s*\((?P<name>\w+)\.(?P<level>#*)(?P<seq>\d+)\)\s*START"
theEnd   = r".*{comment}>>\s*BLOCK\s*\((?P=name)\.(?P=level)(?P=seq)\)\s*END"
theBlock = theStart + r".*" + theEnd
            
aStart = r"{comment}>>\s*BLOCK\s*\(\w+\.#*\d+\)\s*START"
aEnd = r"{comment}>>\s*BLOCK\s*\(\w+\.#*\d+\)\s*END"
aStartOrEnd = r"{comment}>>\s*BLOCK\s*\(\w+\.#*\d+\)\s*(START|END)"

# special comment line (full line)
specialComment = r"^\s*{comment}>>(?P<content>.*)$"
# standard comment line (full line)
standardComment = r"^\s*{comment}"

# Map of the filetype and the single line comment characters
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

class Block:
  """
  This class represents a single block extracted
  from the text.
  """
  def __init__(self,
    name: str = "",
    level: int = 0,
    seq: int = 0, # sequence
    content: str = "",
    comment: str = "//",
    filePath: str = "",
  ) -> None:
    self.name = name
    self.level = level
    self.seq = seq
    self.content = content
    self.comment = comment
    self.filePath = filePath

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

    aStartOrEndPattern = re.compile(aStartOrEnd.format(comment=self.comment))
    specialCommentPattern = re.compile(specialComment.format(comment=self.comment))
    state = 1 # 1 = heading
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
        state = 2
        continue
      elif m and state == 2: # the writeup
        # writeup should immediately follow the start block indicator
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

def extractBlocks(s: str, comment: str= "//") -> List[Block]:
  aStartPattern = re.compile(aStart.format(comment=comment))
  blockPattern = re.compile(theBlock.format(comment=comment), re.DOTALL)

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
            comment=comment,
          )
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

def processAllFiles(directory: str = "../llvm") -> List[Block]:
  counter = 0
  results = []

  directory = osp.abspath(directory)
  allFilePaths = util.getAllFilePaths(directory)

  for filePath in allFilePaths:
    ext = osp.splitext(filePath)[1]
    if ext in fileCommentMap:
      try:
        with open(filePath) as f:
          comment = fileCommentMap[ext]
          tmp = extractBlocks(f.read(), comment) 
          for t in tmp:
            t.filePath = filePath # update the file path
            t.processContent()
          results.extend(tmp)
        counter += 1
      except Exception as e:
        print(e, file=sys.stderr)
        print("File:", filePath, file=sys.stderr)

  print("\nProcessed", counter, "files")
  return results

def printMarkdown(blocks: List[Block]):
  blocks.sort()

  # a tuple of (name, heading) used for docIndex
  namesAndHeadings = []

  baseLevel = 2  # i.e. start from h2
  currName = ""  # current name of the block

  docDetails = io.StringIO()

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

    sourceFileName = osp.basename(block.filePath)
    docDetails.write(f"\n\n[{sourceFileName}](file://{block.filePath})\n\n")

    for codeLine in block.code:
      space = " " * 4
      docDetails.write(f"{space}{codeLine}\n")

  docIndex = io.StringIO()

  docIndex.write("\n\n# Index\n")
  for name, heading in namesAndHeadings:
    docIndex.write(f"\n1. [{heading}](#{name})") 


  docHeading = io.StringIO()
  docHeading.write("# Clang/LLVM Notes\n")
  docHeading.write("These are automatically generated notes from the")
  docHeading.write(" source code of Clang/LLVM 8.0.1.")
  docHeading.write("\n\n") # para change
  docHeading.write("**FIXME** and **TODO** signify some remaining work")

  print(docHeading.getvalue(), end="")
  print(docIndex.getvalue(), end="")
  print(docDetails.getvalue(), end="")
  print("<br><br><br>")
  print("<div class='footer'> <br/> &copy; LEG Team <br/> </div>")


if __name__ == "__main__":
  if sys.argv[0] != "./extract.py":
    print("Error. Note: Run from the location of this script.", file=sys.stderr)
    exit(1)
  blocks = processAllFiles("../llvm")
  printMarkdown(blocks)

