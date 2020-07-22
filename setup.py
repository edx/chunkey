#!/usr/bin/env python
""" Setup to allow pip installs of chunkey module """
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns:
        list: Requirements file relative path strings
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip() for line in open(path).readlines()
            if is_requirement(line.strip())
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.
    Returns:
        bool: True if the line is not blank, a comment, a URL, or an included file
    """
    return line and not line.startswith(('-r', '#', '-e', 'git+', '-c'))


setup(
    name='Chunkey',
    version='1.2.4',
    description='HLS Transport Stream/Encode Pipeline',
    url='http://github.com/edx/chunkey',
    author="edX",
    author_email="oscm@edx.org",
    license="GNU",
    packages=['chunkey'],
    include_package_data=True,
    test_suite='.',
    data_files=[('', ['encode_profiles.json'])],
    install_requires=load_requirements('requirements/base.in'),
    tests_require=load_requirements('requirements/testing.in'),
    zip_safe=False
)
