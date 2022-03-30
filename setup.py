from setuptools import setup, find_packages

setup(
    name='jellyfishlights-py',
    version='0.2.3',
    license='',
    author="Jonathan Nielsen",
    author_email='jonathann@jellyfishlighting.com',
    packages=find_packages(),
    # package_dir={'': 'src'},
    url='https://github.com/vinenoobjelly/jellyfishlights-py',
    keywords='example project',
    install_requires=[
          'websocket-client',
      ],
)