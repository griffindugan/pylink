from setuptools import setup, find_packages
import os
import sys

# Ensure the package is being installed on macOS
if sys.platform != "darwin":
    raise EnvironmentError("This package can only be installed on macOS.")

# Read metadata from __version__.py
metadata = {}
with open(os.path.join('pylink', '__version__.py')) as f:
    exec(f.read(), metadata)

setup(
    name=metadata['__title__'],
    version=metadata['__version__'],
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    description=metadata['__description__'],
    license=metadata['__license__'],
    url=metadata['__url__'],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pylink': ['*.so', 'audio/*.wav'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
    ],
    python_requires='>=3.12',
)