import sys
import os

from setuptools import setup, find_packages

_base = os.path.dirname(os.path.abspath(__file__))
_requirements = os.path.join(_base, 'requirements.txt')
_requirements_test = os.path.join(_base, 'requirements-test.txt')

version = "2.4.21"

install_requirements = []
with open(_requirements) as f:
    install_requirements = f.read().splitlines()

test_requirements = []
if 'test' in sys.argv:
    with open(_requirements_test) as f:
        test_requirements = f.read().splitlines()

setup(
    name="emgcli",
    packages=find_packages(exclude=['ez_setup']),
    version=version,
    install_requires=install_requirements,
    setup_requires=['pytest-runner'],
    tests_require=test_requirements,
    include_package_data=True,
    zip_safe=False,
    test_suite="tests",
    entry_points={
        'console_scripts': [
            'emgcli=emgcli.manage:main',
            'emgdeploy=gunicorn.app.wsgiapp:run',
        ],
    },
)
