import argparse
import extract
import publish
import sys
import os

parser = argparse.ArgumentParser(description='story teller ;)')
group = parser.add_mutually_exclusive_group()
group.add_argument("-p", "--publish", type=str,
                   default=None,
                   help='create a docs folder with html page as well')
group.add_argument('-o', '--outfile', type=str,
                    default='-',
                    help='destination file')
parser.add_argument('sources', type=str, nargs='+',
                    help='the path to sources or includes')
args = parser.parse_args()

# process all sources
blocks = extract.processAllFiles(args.sources[0])

if args.publish is not None:
  # publish a big directory
  publish.cors_free(blocks, args)

# Just create the markdown file
destination = sys.stdout if args.outfile == '-' else open(args.outfile, 'w')
extract.printMarkdown(blocks, destination)

