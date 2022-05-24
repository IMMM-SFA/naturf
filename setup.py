import re
from setuptools import setup, find_packages


def readme():
    """Return the contents of the project README file."""
    with open('README.md') as f:
        return f.read()


def get_requirements():
    """Return a list of package requirements from the requirements.txt file."""
    with open('requirements.txt') as f:
        return f.read().split()


version = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", open('NATURF/__init__.py').read(), re.M).group(1)

setup(
    name='naturf',
    version=version,
    packages=find_packages(),
    url='https://github.com/IMMM-SFA/naturf',
    download_url=f'https://github.com/IMMM-SFA/naturf/archive/refs/tags/v{version}.tar.gz',
    license='MIT',
    author='Levi Sweet-Breu, Melissa Allen-Dumas, Emily Rexer',
    author_email='',
    description='An open-source Python package to address the effect of the geometry of a neighborhood on the local meteorology. ',
    long_description=readme(),
    long_description_content_type="text/markdown",
    python_requires='=3.8.5',
    include_package_data=True,
    install_requires=get_requirements()
)