from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("version.txt", "r") as fh:
    version = fh.read()


setup(name='hplib',
      version=version,
      description='Python (3) usefull classes for mysql database en sending emails',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/hpharmsen/hplib',
      author='HP Harmsen',
      author_email='hp@harmsen.nl',
      license='THE UNLICENCE',
      packages=['hplib'],
      install_requires=['configparser','pymysql','pyyaml'],
      classifiers=[
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: The Unlicense",
            "Operating System :: OS Independent",
      ],
      zip_safe=False)
