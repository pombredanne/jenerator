"""
Functions to handle transforming various input formats into HTML to be fed into
a template.
"""

import os
import csv # CSV
from markdown import markdown # Markdown
from docutils.core import publish_parts # reStructureText


MDEXTS = ('md', 'markdown')
RSTEXTS = ('rst',)
CSVEXTS = ('csv', 'tsv')
TXTEXTS = ('txt',)
HTMLEXTS = ('html', 'htm')


def process_md(path):
    with open(path, 'r') as f:
        content = ''.join(f.readlines())
    return content, markdown(content)

def process_rst(path):
    with open(path, 'r') as f:
        content = ''.join(f.readlines())
    return content, publish_parts(content, writer_name='html')['body']

def process_csv(path):
    # TODO: Handle comments, turn them into top content
    # TODO: Handle blank lines and other crap csv fails on
    sniffer = csv.Sniffer()
    with open(path, 'r') as f:
        raw = ''.join(f.readlines())
        f.seek(0)
        sample = f.read(4096)
        headers = sniffer.has_header(sample)
        dialect = sniffer.sniff(sample)
        f.seek(0)
        reader = csv.reader(f, dialect=dialect)
        output = '<table>'
        if headers:
            output += '<thead><tr><th>'
            output += '</th><th>'.join(next(reader))
            output += '</th></tr></thead>'
        output += '<tbody>'
        for row in reader:
            output += '<tr><td>'
            output += '</td><td>'.join(row)
            output += '</td></tr>'
        output += '</tbody></table>'
    return raw, output


def process_txt(path):
    with open(path, 'r') as f:
        raw = ''.join(f.readlines())
    content = '<p>' + raw.replace('\n', '\n<br>') + '</p>'
    return raw, content


def process_html(path):
    with open(path, 'r') as f:
        raw = ''.join(f.readlines())
    return raw, raw


def process(path):
    ext = os.path.splitext(path)[1][1:]
    if ext in MDEXTS:
        return process_md(path)
    if ext in RSTEXTS:
        return process_rst(path)
    if ext in CSVEXTS:
        return process_csv(path)
    if ext in TXTEXTS:
        return process_txt(path)
    if ext in HTMLEXTS:
        return process_html(path)
