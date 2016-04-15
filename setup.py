from setuptools import setup
from setuptools import find_packages

setup(name='betago',
      version='0.1',
      description='Create your own go bot from scratch. We are Lee Sedol!',
      url='http://github.com/maxpumperla/betago',
      download_url='https://github.com/maxpumperla/betago/tarball/0.1',
      author='Max Pumperla',
      author_email='max.pumperla@googlemail.com',
      install_requires=['keras', 'gomill', 'flask', 'flask-cors', 'future', 'h5py'],
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
