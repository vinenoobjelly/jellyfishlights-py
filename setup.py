from setuptools import setup, find_packages
from pathlib import Path
# https://realpython.com/pypi-publish-python-package/

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='jellyfishlights-py',
    version='0.8.0',
    license='',
    author="Jonathan Nielsen",
    author_email='jonathann@jellyfishlighting.com',
    packages=find_packages(),
    # package_dir={'': 'src'},
    url='https://github.com/vinenoobjelly/jellyfishlights-py',
    keywords='',
    install_requires=[
          'websocket-client',
      ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    description='Python library for controlling Jellyfish Lights via the local network.',
)