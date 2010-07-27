# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='daffy',
    version='0.1',
    zip_safe=True,
    description='Runtime environment for Daffy: a dataflow programming language',
    author='Lorenzo Pierfederici',
    author_email='lpierfederici@gmail.com',
    #url='',
    license='GPL v3',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    package_data={'daffy': []},
)
