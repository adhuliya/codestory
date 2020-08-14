from typing import List, Dict, Optional
import os
import os.path as osp
import io
import pickle
import sys
from mistune import mistune

import extract
import common_util as cutil
import util as util

SKEL_DIR_NAME = "skel"
DATABASE_DIR = ".codestory"
CACHE_FILE_NAME = "document.pickle"
MARKDOWN_FILE_NAME = "document.md"
HEADER_FILE_NAME = ".header.html"
FOOTER_FILE_NAME = ".footer.html"
HTML_FILE_NAME = "document.html"

class Document:
  """Stores the document information that is (to be) published."""
  def __init__(self,
               title: str = "CodeStory",
               author: str = "CodeStory",
  ) -> None:
    self.title = title
    self.author = author
    self.index: str = ""
    self.contents: str = ""
    self.publicationDir: str = None # the directory where to create the doc
    self.sourceDir: str = None # the directory that was searched
    self.header: str = None
    self.footer: str = None
    # Has the cache changed?
    self.changed: bool = False
    # The index and contents in markdown format
    self.docIndex: io.StringIO = None
    self.docDetails: io.StringIO = None

    self.cachedPrefix: Optional[util.AbsFilePathT] = ""
    self.cachedFileInfoMap:\
      Optional[Dict[util.AbsFilePathT, extract.FileInfo]] = {}
    self.cachedFileBlocksMap:\
      Optional[Dict[util.AbsFilePathT, List[extract.Block]]] = {}

  def processDirectory(self,
                       dirPath: cutil.RelFilePathT
  ) -> None:
    """Get all blocks from all the files in the given directory."""
    counter = 0

    absDirPath = osp.abspath(dirPath)

    prefixLen = len(absDirPath) + 1
    for absFilePath in cutil.getAllFilePaths(absDirPath):
      if not osp.exists(absFilePath):
        continue
      if osp.isdir(absFilePath) or cutil.isBinaryFile(absFilePath):
        # don't process directories and binary files
        continue

      fileInfo = extract.FileInfo(absFilePath)

      if self.isCached(fileInfo, absDirPath):
        pass
      else:
        counter += 1
        relFilePath = absFilePath[prefixLen:]
        self.cachedFileInfoMap[relFilePath] = fileInfo
        blocks = extract.extractBlocksFromFile(absFilePath)
        for b in blocks:
          b.fileInfo = fileInfo # update the file path
          b.processContent()
        blocks.sort()
        self.cachedFileBlocksMap[fileInfo.filePath] = blocks

    print("\nCodeStory: Processed", counter, "new files.")

  def generateMarkdown(self):
    # STEP 1: Collect all blocks in one list
    allBlocks = []
    for blockList in self.cachedFileBlocksMap.values():
      allBlocks.extend(blockList)

    # STEP 2: Call the main logic
    self.docIndex, self.docDetails = extract.makeMarkdown(allBlocks)

  def isCached(self,
               fileInfo: extract.FileInfo,
               prefix: cutil.AbsFilePathT
  ) -> bool:
    cached = False
    prefixLen = len(prefix) + 1
    relFilePath = fileInfo.filePath[prefixLen:]
    if relFilePath in self.cachedFileInfoMap:
      oldFileInfo = self.cachedFileInfoMap[relFilePath]
      if oldFileInfo.mtime_ns >= fileInfo.mtime_ns:
        cached = True
    return cached

  @classmethod
  def serialize(cls,
                doc: "Document",
                filePath: cutil.RelFilePathT,
  ) -> None:
    with open(filePath, "wb") as file:
      pickle.dump(doc, file)

  @classmethod
  def deSerialize(cls,
                  filePath: cutil.RelFilePathT,
  ) -> "Document":
    with open(filePath, "rb") as file:
      doc: Document = pickle.load(file)
      return doc

def dumpCache(doc: Document, dirPath: cutil.RelFilePathT) -> None:
  absDirPath = cutil.getAbolutePath(dirPath)

  absDataDirPath = osp.join(absDirPath, DATABASE_DIR)
  cutil.createDir(absDataDirPath)

  cacheFilePath = osp.join(absDataDirPath, CACHE_FILE_NAME)
  absCacheFilePath = osp.join(absDirPath, cacheFilePath)

  doc.serialize(doc, absCacheFilePath)

def loadCache(dirPath: cutil.RelFilePathT) -> Document:
  """Loads cached Document and returns the object,
  else returns a fresh Document object.
  """
  absDirPath = cutil.getAbolutePath(dirPath)
  cacheFilePath = osp.join(DATABASE_DIR, CACHE_FILE_NAME)
  absCacheFilePath = osp.join(absDirPath, cacheFilePath)

  if not osp.exists(absCacheFilePath):
    print("CodeStory: No cache found!", file=sys.stderr)
    return Document()  # return a fresh document (no cache found)
  else:
    return Document.deSerialize(absCacheFilePath)

def publishMarkdown(doc: Document,
                    destDirPath: cutil.RelFilePathT
) -> None:
  absDestDirPath = cutil.getAbolutePath(destDirPath)

  doc.generateMarkdown() #MUST

  absMarkdownFilePath = osp.join(absDestDirPath, MARKDOWN_FILE_NAME)

  with open(absMarkdownFilePath, "w") as file:
    file.write(doc.docIndex.getvalue())
    file.write(doc.docDetails.getvalue())

def publishHtml(doc: Document,
                dirPath: cutil.RelFilePathT
) -> None:
  """
  Assumption: doc.generateMarkdown() has been already called.
  """

  absDirPath = cutil.getAbolutePath(dirPath)

  headerFilePath = osp.join(absDirPath, HEADER_FILE_NAME)
  headerContent = cutil.readFromFile(headerFilePath)

  footerFilePath = osp.join(absDirPath, FOOTER_FILE_NAME)
  footerContent = cutil.readFromFile(footerFilePath)

  htmlFilePath = osp.join(absDirPath, HTML_FILE_NAME)

  with open(htmlFilePath, "w") as file:
    # Write header
    file.write(headerContent.format(title="CodeStory", author="CodeStory"))

    # Write index
    indexMarkdown = doc.docIndex.getvalue()
    file.write(mistune.html(indexMarkdown))

    # Write details
    detailsMarkdown = doc.docDetails.getvalue()
    file.write(mistune.html(detailsMarkdown))

    # Write footer
    file.write(footerContent)
