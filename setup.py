from setuptools import setup, find_packages

setup(

    name='geod',
    version='0.1.0',
    description='GEO directory IO for Maya/Houdini.',
    url='http://github.com/mikeboers/geod',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    
    author='Mike Boers',
    author_email='geod@mikeboers.com',
    license='BSD-3',
    
)