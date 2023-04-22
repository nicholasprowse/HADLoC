from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

setup(
    name='hadloc',
    version='0.0.2',
    author='Nic Prowse',
    author_email='john.doe@foo.com',
    license='GNU General Public License v3.0',
    description='Command line tool to build, emulate and load programs for the HaDLOC 8-bit computer',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/nicholasprowse/HADLoC',
    py_modules=['controller', 'app'],
    packages=find_packages(),
    install_requires=[requirements],
    python_requires='>=3.11',
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    entry_points='''
        [console_scripts]
        hadloc=controller:main
    ''',
    include_package_data=True
)
