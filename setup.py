import sys

from setuptools import setup, find_packages

version = "0.1.0"

install_requirements = []
with open('requirements.txt') as f:
    install_requirements = f.read().splitlines()

test_requirements = []
if "test" in sys.argv:
    with open('requirements-test.txt') as f:
        test_requirements = f.read().splitlines()

sys.path.insert(0, 'emg')

setup(
    name="emg",
    packages=find_packages(exclude=['ez_setup']),
    version=version,
    install_requires=install_requirements,
    setup_requires=['pytest-runner'],
    tests_require=test_requirements,
    include_package_data=True,
    zip_safe=False,
    test_suite="tests",
)
