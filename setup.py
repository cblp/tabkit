#!/usr/bin/env python

import os, shutil

#from distutils.core import setup, Extension
from distutils.command.clean import clean
from distutils.command.build import build

from _compile_tools import main

from setuptools import setup
from setuptools import Extension
#from distutils.core import setup
#from distutils.core import Extension

class my_clean(clean):
    def run(self):
        clean.run(self)
        shutil.rmtree('tabkit.egg-info', ignore_errors=True)

class my_build(build):
    def run(self):
        build.run(self)
        main(self.build_scripts)

setup(
    name = 'tabkit',
    version = '1.1',
    description = 'python wrappers around coreutils (cat, join, sort, cut), awk and pv to support tab-separated files with headers.',
    author = 'Alexey Akimov',
    author_email = 'akimov@yandex-team.ru',
    packages = ['tabkit'],
    scripts = [
        'yacontext-bash-common/yacontext-bash-common.sh'
    ],
    ext_modules = [
        Extension(
            'tabkit._tparallel',
            sources=['tabkit/_tparallel.cpp'],
            extra_compile_args = ['-finput-charset=UTF-8', '-ffast-math']
        )
    ],
    cmdclass = {
        'clean': my_clean,
        'build': my_build,
    },
)

