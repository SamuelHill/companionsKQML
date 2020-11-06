# -*- coding: utf-8 -*-
# @Author: Samuel Hill
# @Date:   2020-02-13 14:50:39
# @Last Modified by:    Samuel Hill
# @Last Modified time:  2020-11-04 19:12:50

from setuptools import setup

setup(name='companionsKQML',
      version='1.1.2',
      packages=['companionsKQML'],
      python_requires='>=3.0',
      install_requires=['pykqml>=1.3', 'psutil>=5.6.5',
                        'python-dateutil>=2.8.1'],
      url='http://github.com/SamuelHill/companionsKQML',
      author='Samuel J. Hill',
      author_email='samuelhill2022@northwestern.edu',
      description='Companions agents in Python.',
      long_description=open('README.md', 'r').read(),
      long_description_content_type='text/markdown',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          ],
      project_urls={
          'Qualitative Reasoning Group': 'http://www.qrg.northwestern.edu/'
          }
      )
