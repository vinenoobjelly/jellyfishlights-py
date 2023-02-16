from setuptools import setup, find_packages
# https://realpython.com/pypi-publish-python-package/

setup(
    name='jellyfishlights-py',
    version='0.6.0',
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
)