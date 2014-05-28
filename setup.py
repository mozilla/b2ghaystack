# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from setuptools import setup

# get documentation from the README
try:
    here = os.path.dirname(os.path.abspath(__file__))
    description = file(os.path.join(here, 'README.md')).read()
except (OSError, IOError):
    description = ''

setup(name='b2ghaystack',
      version='0.1',
      description='Trigger Jenkins jobs for B2G builds between revisions',
      long_description='A command line tool to assist in searching for B2G '
                       'regressions by triggering jobs in Jenkins for each '
                       'build between two revisions.',
      classifiers=[],
      keywords='mozilla b2g boot2gecko firefoxos regression',
      author='Dave Hunt',
      author_email='dhunt@mozilla.com',
      url='https://github.com/mozilla/b2ghaystack',
      license='Mozilla Public License 2.0 (MPL 2.0)',
      packages=['b2ghaystack'],
      entry_points={
          'console_scripts':
              ['b2ghaystack = b2ghaystack.b2ghaystack:cli']},
      install_requires=[
          'beautifulsoup4==4.3.2',
          'python-jenkins==0.2.1',
          'requests==2.2.1',
          'futures==2.1.6'])
