from setuptools import setup
from setuptools import find_packages

setup(name='omegago',
      version='0.0.1',
      description="Alphago's idiot brother",
      url='http://github.com/maxpumperla/omegago',
      download_url='https://github.com/maxpumperla/omegago/tarball/0.0.1',
      author='Max Pumperla',
      author_email='max.pumperla@googlemail.com',
      install_requires=['keras', 'gomill'],
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
