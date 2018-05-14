
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='Chunkey',
    version='1.2.3',
    description='HLS Transport Stream/Encode Pipeline',
    url='http://github.com/edx/chunkey',
    author="edX",
    author_email="oscm@edx.org",
    license="GNU",
    packages=['chunkey'],
    include_package_data=True,
    install_requires=[
        'boto',
        'requests',
        'pyyaml'
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    data_files=[('', ['encode_profiles.json'])],
    zip_safe=False
)
