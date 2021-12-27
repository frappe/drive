from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in drive/__init__.py
from drive import __version__ as version

setup(
	name="drive",
	version=version,
	description="An easy to use, document sharing and management solution.",
	author="mituldavid",
	author_email="mituldavid@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
