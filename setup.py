from setuptools import setup, find_packages

setup(
    name="PyCoD",
    version="0.1.0",
    author="SE2Dev",
    author_email="no-reply@github.com",
    url="https://github.com/SE2Dev/PyCoD",
    packages=find_packages(where="src"),
    package_dir={
        "": "src"
    }
)
