#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def recursive_requirements(requirement_file, libs, links, path=''):
    if not requirement_file.startswith(path):
        requirement_file = os.path.join(path, requirement_file)
    with open(requirement_file) as requirements:
        for requirement in requirements.readlines():
            if requirement.startswith('-r'):
                requirement_file = requirement.split()[1]
                if not path:
                    path = requirement_file.rsplit('/', 1)[0]
                recursive_requirements(requirement_file, libs, links,
                                       path=path)
            elif requirement.startswith('-f'):
                links.append(requirement.split()[1])
            else:
                libs.append(requirement)


with open('README.rst') as readme:
    long_description = readme.read()


libraries, dependency_links = [], []
recursive_requirements('requirements.txt', libraries, dependency_links)


setup(
    name = "django-workflow-activity",
    version = "1.0.2",
    packages = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),

    install_requires=libraries,
    dependency_links=dependency_links,
    include_package_data=True,
    long_description=long_description,
    author = 'Arnaud Grausem',
    author_email = 'arnaud.grausem@unistra.fr',
    description = 'Manage all events on workflows',
    keywords = "workflows django events log",
    url = 'https://github.com/unistra/django-workflow-activity',

    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],

)
