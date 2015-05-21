#!/usr/bin/env python

import fnmatch
import glob
import os
import sys

from setuptools import setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

VERSION = "2.0.0"

setup(
    name='cesspool',
    version=VERSION,
    description='Centralized File Downloader',
    author='Zach Banks',
    author_email='zbanks@mit.edu',
    url='https://github.com/ervanalb/cesspool',
    packages=[
        'cesspool', 
        'cesspool.downloaders', 
    ],
    download_url="https://github.com/ervanalb/cesspool/tarball/{}".format(VERSION),
    zip_safe=False,
    install_requires=required,
    scripts=[
        #"bin/cesspool", 
    ],
    package_dir = {
    },
    package_data={
        'cesspool': [
            "../supervisord.conf", 
            "../requirements.txt", 
            "../settings.json",
            '../www/index.html', 
            '../www/assets/*.js', 
            '../www/assets/*.otf', 
            '../www/assets/*.css', 
            '../www/assets/images/*'
        ],
    },
)
