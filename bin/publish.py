from typing import List, Dict
import os, os.path
import io
import extract

FILE = os.path.realpath(__file__)
template_dir = os.path.join(os.path.dirname(FILE), '..', 'docs', 'autogen')

def concatStreams(streams: List[io.StringIO]) -> str:
  flat = '\n'.join([x.getvalue() for x in streams])
  return '`{}`'.format(flat.replace('`', '\`'))

def cors_free(blocks: List[extract.Block], args: Dict):
  print(concatStreams(extract.makeMarkdown(blocks)))
  os.makedirs(args.publish, exist_ok=True)
  destination = open('{}/notes.md'.format(args.publish), 'w')
  extract.printMarkdown(blocks, destination)
  os.system('cp -r {} {}'.format(os.path.join(template_dir, 'static'),
                                 args.publish))
  with open(os.path.join(template_dir, 'notes_cors_free.html'), 'r') as fin:
    with open(os.path.join(args.publish, 'notes.html'), 'w') as fout:
      text = fin.read()
      fout.write(text.replace('MARKDOWN_FILE_CONTENT',
                              concatStreams(extract.makeMarkdown(blocks))))
