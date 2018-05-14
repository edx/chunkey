
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='Chunkey',
    version='1.2.3',
    description='HLS Transport Stream/Encode Pipeline',
    url='http://github.com/yro/chunkey',
    author='@yro',
    author_email='greg@willowgrain.io',
    license='GNU',
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
