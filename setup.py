#!/usr/bin/env python
import codecs
import os
from glob import glob
from os.path import basename
from os.path import splitext
from setuptools import setup, find_packages


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-codecov',
    version='0.4.0',
    author='David Salvisberg',
    author_email='david.salvisberg@seantis.ch',
    maintainer='David Salvisberg',
    maintainer_email='david.salvisberg@seantis.ch',
    license='MIT',
    url='https://github.com/seantis/pytest-codecov',
    description='Pytest plugin for uploading pytest-cov results to codecov.io',
    long_description=read('README.rst'),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=[
        'pytest>=4.6.0',
        'pytest-cov>=2.11.0',
        'coverage[toml]>=5.2.1',
        'requests>=2.25.1'
    ],
    tests_require=[
        'GitPython>=3.1.15'
    ],
    extras_require={
        'git': [
            'GitPython>=3.1.15'
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'codecov = pytest_codecov',
        ],
    },
)
