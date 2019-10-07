from typing import List, Dict
import os, os.path
import extract

FILE = os.path.realpath(__file__)
template_dir = os.path.join(os.path.dirname(FILE), '..', 'docs', 'autogen')

def cors_free(blocks: List[extract.Block], args: Dict):
  os.makedirs(args.publish, exist_ok=True)
  destination = open('{}/notes.md'.format(args.publish), 'w')
  extract.printMarkdown(blocks, destination)
  os.system('cp -r {} {}'.format(os.path.join(template_dir, 'static'),
                                 args.publish))
  os.system('cp {} {}'.format(os.path.join(template_dir, 'notes_cors_free.html'),
                              os.path.join(args.publish, 'notes.html')))
