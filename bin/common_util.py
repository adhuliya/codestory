#!/usr/bin/env python3

# MIT License
# Copyright (c) 2019 Anshuman Dhuliya

"""Common utility functions module which can be used in any project.
Originalfile: $MYDATA/git/ws/ws-misc-git/python/mylib/util/common_util.py
Note: This file has been hard linked at many places.
"""

import os
import os.path as osp
from io import StringIO
import subprocess as subp
from typing import Optional, List

import logging
_log = logging.getLogger(__name__)

globalCounter: int = 0
RelFilePathT = str  # a relative file path (could be absolute too)
AbsFilePathT = str  # an absolute file path
textChars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})

# used in calculation of line number
lastStr = ""
lastPos = 0
lastLineCount = 0

def createDir(dirPath, existOk=True):
  """Creates dir. Relative paths use current directory.

  Args:
    dirPath: an absolute or relative path

  Returns:
    str: absolute path of the directory or None.
  """
  absPath = getAbolutePath(dirPath)
  _log.debug("Creating directory %s", absPath)

  try:
    os.makedirs(absPath, exist_ok=existOk)
  except Exception as e:
    _log.error("Error creating directory {},\n{}".format(absPath, e))
    return None

  return absPath

def getAbolutePath(filePath: str):
  """Returns absolute path of the given file."""
  if osp.isabs(filePath):
    absPath = filePath
  else:
    cwd = os.getcwd()
    absPath = osp.join(cwd, filePath)
  return absPath

def getUniqueId() -> int:
  """Returns a unique integer id (increments by 1)."""
  # use of simple function and a global var is runtime efficient.
  global globalCounter
  globalCounter += 1
  return globalCounter

def readFromFile(fileName: str) -> str:
  """Returns the complete content of the given file."""
  with open(fileName) as f:
    return f.read()

def writeToFile(fileName: str, content: str):
  """Writes content to the given file."""
  with open(fileName, "w") as f:
    f.write(content)
  return None

def appendToFile(fileName: str, content: str):
  """Writes content to the given file."""
  with open(fileName, "a") as f:
    f.write(content)
  return None

def hexToFloat(hexVal) -> float:
  """Convert a float hex representation 0x41b80000 to a real float value"""
  import struct
  if isinstance(hexVal, str):
    return struct.unpack("!f", struct.pack("!i", int(hexVal, 16)))[0]
  elif isinstance(hexVal, int):
    return struct.unpack("!f", struct.pack("!i", hexVal))[0]

def hexToDouble(hexVal) -> float:
  """Convert a float hex representation 0x41b80000 to a real double value"""
  import struct
  if isinstance(hexVal, str):
    return struct.unpack("!d", struct.pack("!q", int(hexVal, 16)))[0]
  elif isinstance(hexVal, int):
    return struct.unpack("!d", struct.pack("!q", hexVal))[0]

def randomString(length: int = 10,
                 digits: bool = True,
                 caps: bool = True,
                 small: bool = True,
) -> Optional[str]:
  """Returns a random string of given length."""
  import random
  import string
  if not (digits or caps or small): return None

  randDigits = random.choices(string.digits, k=length)
  randCaps = random.choices(string.ascii_uppercase, k=length)
  randSmall = random.choices(string.ascii_lowercase, k=length)

  collect = []
  if digits:
    collect = randDigits
  if caps:
    collect.extend(randCaps)
  if small:
    collect.extend(randSmall)

  random.shuffle(collect)

  return "".join(collect[:length])

def getAllFilePaths(directory: str) -> List[str]:
  """Returns the full file names of all the files
  (recursively) withing the given directory."""
  for root, dirs, files in os.walk(directory):
    for d in dirs:
      path = osp.join(root, d)
      yield path
    for f in files:
      path = osp.join(root, f)
      yield path

def getUserName() -> str:
  return os.environ.get("USER", "Anonymous")

def getFileModTimeInNanoSecs(filePath: str) -> int:
  stat = os.stat(filePath, follow_symlinks=True)
  return stat.st_mtime_ns

def calcLineNum(s: str, pos: int) -> int:
  """Calculates the line number of the given pos in
  the string s. It optimizes by caching the last
  calculated result."""
  global lastStr, lastPos, lastLineCount
  if s != lastStr:
    lastStr = s
    lastPos = 0
    lastLineCount = 1
  for i in range(lastPos, pos):
    if s[i] == os.linesep:
      lastLineCount += 1
  return lastLineCount

def isEmptyDir(directory: str) -> bool:
  lst = os.listdir(directory)
  return len(lst) == 0

def isBinaryFile(filePath: RelFilePathT) -> bool:
  isBinaryString = lambda bytes: bool(bytes.translate(None, textChars))
  return isBinaryString(open(filePath, "rb").read(1024))

def getScriptRelativeFilePath(relFileName: str) -> str:
  """Takes a relative file name and
  returns an absolute path using the location of
  this script.
  """
  if osp.isabs(relFileName):
    print("ERROR: relative file name exptected:", relFileName)
    return None
  thisScriptPath = osp.realpath(__file__)
  thisScriptDir = osp.dirname(thisScriptPath)
  absFilePath = osp.join(thisScriptDir, relFileName)
  return absFilePath

def copyDirectoryContents(srcDir: RelFilePathT, destDir: RelFilePathT) -> None:
  """Copies the contents of the source directory
  into the destination directory.
  It assumes that the source and destination directories exist.
  """
  filePathList = os.listdir(srcDir)
  for filePath in filePathList:
    absFilePath = osp.join(srcDir, filePath)
    subp.run(f"cp -r {absFilePath} {destDir}", shell=True)

def copyFile(filePath: RelFilePathT, destDir: RelFilePathT) -> None:
  subp.run(f"cp -r {filePath} {destDir}", shell=True)

def prepareDestinationDirectory(
    srcDirPath: RelFilePathT,
    destDirPath: RelFilePathT,
) -> None:
  """
  It tries to copy the contents of source directory to the
  destination directory without overwriting.
  Assumption: source directory exists.
  """
  # STEP 0: get absolute paths (optional)
  absDestDirPath: AbsFilePathT \
    = getAbolutePath(destDirPath)
  absSrcDirPath: AbsFilePathT \
    = getAbolutePath(srcDirPath)

  # STEP 1: create the destination dir if doesn't exist
  createDir(absDestDirPath)

  # STEP 2: Systematically copy the contents of source dir to destination dir
  if isEmptyDir(absDestDirPath):
    # STEP 3.1: If destination dir is empty copy the whole source dir
    copyDirectoryContents(absSrcDirPath, absDestDirPath)
  else:
    # STEP 3.2:
    # Selectively copy files if they don't exist in the destination dir
    prefixLen = len(absSrcDirPath) + 1
    for absSrcFilePath in getAllFilePaths(absSrcDirPath):
      relFilePath = absSrcFilePath[prefixLen:] # remove prefix
      relDirPath = osp.dirname(relFilePath)
      absFilePath = osp.join(absDestDirPath, relFilePath)
      absDirPath = osp.join(absDestDirPath, relDirPath)

      if not osp.exists(absDirPath):
        createDir(absDestDirPath)

      if not osp.exists(absFilePath):
        copyFile(absSrcFilePath, absDirPath)

