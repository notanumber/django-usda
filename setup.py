import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-usda',
    version='0.1.0beta',
    description='Import and map the USDA National Nutrient Database for Standard Reference (SR22) to Django models',
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django',
    ],
    author='David Sauve',
    author_email='dsauve@gmail.com',
    url='http://github.com/notanumber/django-usda',
    license='http://www.opensource.org/licenses/bsd-license.php',
    packages=[
        'usda',
        'usda.management',
        'usda.management.commands',
    ],
)
