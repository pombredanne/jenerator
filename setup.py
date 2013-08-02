#!/usr/bin/env python3

from distutils.core import setup

ver = open('VERSION', 'r').read().strip()

setup(
        name='jenerator',
        version=ver,
        description='Static site generator',
        author='George Lesica',
        author_email='george@lesica.com',
        url='http://www.github.com/glesica/jenerator',
        packages=['jenerator'],
        package_data={'jenerator': ['skel/*']},
        requires=['markdown','jinja2'],
        scripts=['scripts/jen']
)
