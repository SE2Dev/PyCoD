import os.path
import re

from setuptools import setup, find_packages


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version_raw(rel_path):
    rxVersion = "\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*\\)"
    rxVersionLine = "^\\s*__version__\\s*=\\s*" + rxVersion + "(?:\\s*#.*)?"
    for line in read(rel_path).splitlines():
        match = re.search(rxVersionLine, line, re.IGNORECASE)
        if match:
            return (int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)))
    else:
        raise RuntimeError("Unable to find version string.")


def get_version(rel_path):
    version = get_version_raw(rel_path)
    return ".".join([str(part) for part in version])


setup(
    name="PyCoD",
    version=get_version("./src/PyCoD/__init__.py"),
    author="SE2Dev",
    author_email="no-reply@github.com",
    url="https://github.com/SE2Dev/PyCoD",
    packages=find_packages(where="src"),
    package_dir={
        "": "src"
    }
)
