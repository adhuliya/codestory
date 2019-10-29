#!/usr/bin/env python3

import argparse
import extract
import publish
import sys
import common_util as cutil
import os.path as osp

# STEP 0: Define Command Line Arguments
parser = argparse.ArgumentParser(description='Write stories in your code ;)')
#group = parser.add_mutually_exclusive_group()
parser.add_argument("-p", "--publish", type=str,
                    default="codestory",
                    help='create PUBLISH folder with markdown and html pages')
parser.add_argument("source", type=str,
                    default = "src",
                    help='the path to source dir to be processed')

# STEP 1: Parse the arguments
args = parser.parse_args()

# STEP 2: Prepare the directory to publish in
skelDir = cutil.getScriptRelativeFilePath(publish.SKEL_DIR_NAME)
cutil.prepareDestinationDirectory(skelDir, args.publish)

# STEP 3: Load the cache
doc = publish.loadCache(args.publish)

# STEP 4: Process the source directory
if not osp.exists(args.source):
  print("CodeStory: ERROR:", args.source, "directory doesn't exist!", file=sys.stderr)
  exit(1)
doc.processDirectory(args.source)

# STEP 5: Create the markdown file
publish.publishMarkdown(doc, args.publish)

# STEP 6: Create the HTML File
publish.publishHtml(doc, args.publish)

# STEP 7: Save the cache in the publish directory
publish.dumpCache(doc, args.publish)

# DONE :).
