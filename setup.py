"""
Rekt GooglePlaces
=================

rekt is a wrapper around the requests library that makes generic rest
operations less painful. Rekt GooglePlaces contains specific improvesments for working with googleplaces.
"""
import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('rekt_googleplaces/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if len(line.strip())]
    requirements = [r for r in requirements if not any([r.startswith('git'), r.startswith('http')])]

setup(
    name='rekt-googleplaces',
    version=version,
    url='http://github.com/vengefuldrx/rekt-googleplaces/',
    license='Apache License Version 2',
    author='Dillon Hicks',
    author_email='chronodynamic@gmail.com',
    description="A requests wrapper library for dynamically generating rest clients for Google's Places API",
    long_description=__doc__,
    packages=['rekt_googeplaces'],
    package_data={'rekt_googleplaces' : ['specs/*.yaml']},
    include_package_data=True,
    platforms='any',
    install_requires=[
        'requests',
        'PyYaml',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
        [console_scripts]
        rekt=rekt:main
    '''
)
