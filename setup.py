import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()

with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = ['WebTest', 'WebTestRecorder']


setup(name='WebTestPlus',
      version='0.1',
      description='Helper to test WSGI applications',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Mozilla Services',
      author_email='services-dev@mozilla.org',
      url='https://github.com/mozilla-services/webtestplus',
      keywords='web webtest test',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="webtest")
