from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

setup(
    name='hadloc',
    version='0.1.1',
    author='Nic Prowse',
    license='GNU General Public License v3.0',
    description='Command line tool to build, emulate and load programs for the HaDLOC 8-bit computer',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/nicholasprowse/HADLoC',
    py_modules=['hadloc'],
    packages=find_packages(),
    install_requires=[requirements],
    python_requires='>=3.11',
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Topic :: Software Development :: Assemblers",
        "Topic :: Software Development :: Compilers",
        "Topic :: System :: Emulators"
    ],
    entry_points='''
        [console_scripts]
        hadloc=hadloc.__main__:main
    ''',
    include_package_data=True
)
