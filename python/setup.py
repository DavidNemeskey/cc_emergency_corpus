#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

# I used the following resources to compile the packaging boilerplate:
# https://python-packaging.readthedocs.io/en/latest/
# https://packaging.python.org/distributing/#requirements-for-packaging-and-distributing

from setuptools import find_packages, setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='cc_emergency',
      version='0.9.1',
      description='Scripts and tools for emergency corpus building',
      long_description=readme(),
      url='https://github.com/DavidNemeskey/cc_emergency_corpus',
      author='Dávid Márk Nemeskey',
      license='MIT',
      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 3 - Alpha',

          # Indicate who your project is intended for
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: Information Analysis',
          # This one is not in the list...
          'Topic :: Scientific/Engineering :: Natural Language Processing',

          # Environment
          'Operating System :: POSIX :: Linux',
          'Environment :: Console',
          'Natural Language :: English',

          # Pick your license as you wish (should match "license" above)
           'License :: OSI Approved :: MIT License',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6'
      ],
      keywords='emergency corpus',
      packages=find_packages(exclude=['scripts']),
      # Include the configuration -- unfortunately, MANIFEST.in doesn't seem
      # to do it for bdist (and package_data for sdist)
      package_data={
          'cc_emergency.conf': ['*'],
      },
      # Install the scripts
      scripts=[
          'scripts/run_pipeline.py',
      ],
      # Tensorflow and numpy can be installed from requirement files, as they
      # are only required if the nn module / scripts are used.
      install_requires=[
          # Duplicate detection
          'datasketch',
          # Python 2/3 compatibility
          'future', 'six',
          # ExitStack for Python 3.3-
          'contextlib2',
          # Language identification
          'cld2-cffi', 'langid',
          # An earlier version was broken (don't remember which); also,
          # iterparse is broken in 3.7.3. :)
          'lxml==3.6.4',
          # For the embedding stuff
          'networkx',
          # For stopword filtering
          'nltk',
          # Computations
          'numpy', 'scipy', 'sklearn', 'pandas',
          # For networking
          'requests',
          # For domain filtering
          'tldextract'
      ],
      # zip_safe=False,
      use_2to3=False)
