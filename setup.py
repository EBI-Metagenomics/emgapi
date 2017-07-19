import sys
import os

from setuptools import setup, find_packages

_base = os.path.dirname(os.path.abspath(__file__))
_requirements = os.path.join(_base, 'requirements.txt')
_requirements_test = os.path.join(_base, 'requirements-test.txt')

version = "0.1.0"

install_requirements = []
with open(_requirements) as f:
    install_requirements = f.read().splitlines()

test_requirements = []
if "test" in sys.argv:
    with open(_requirements_test) as f:
        test_requirements = f.read().splitlines()

sys.path.insert(0, 'emg')

setup(
    name="emgapi",
    packages=find_packages(
        exclude=['ez_setup', 'tests', 'docker', 'database', 'nginx']),
    version=version,
    install_requires=install_requirements,
    setup_requires=['pytest-runner'],
    tests_require=test_requirements,
    include_package_data=True,
    zip_safe=False,
    test_suite="tests",
)
