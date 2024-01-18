import re
from setuptools import setup, find_packages


def readme():
    """Return the contents of the project README file."""
    with open("README.md") as f:
        return f.read()


version = re.search(
    r"__version__ = ['\"]([^'\"]*)['\"]", open("naturf/__init__.py").read(), re.M
).group(1)

setup(
    name="naturf",
    version=version,
    packages=find_packages(),
    url="https://github.com/IMMM-SFA/naturf",
    license="MIT",
    author="Levi Sweet-Breu, Melissa Allen-Dumas, Chris R. Vernon, Emily Rexer",
    author_email="",
    description="An open-source Python package to address the effect of the geometry of a neighborhood on the local meteorology. ",
    long_description=readme(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8.5",
    include_package_data=True,
    install_requires=[
        "numpy>=1.22.4",
        "pandas>=1.4.2",
        "geocube>=0.3.1",
        "rasterio>=1.2.10",
        "xarray>=2022.3.0",
        "joblib>=1.0.1",
        "fiona>=1.8.19",
        "pyproj>=3.0.1",
        "rtree>=1.0.0",
        "shapely>=1.8.2,<2",
        "geopandas>=0.10.2",
        "sf-hamilton[visualization]>=1.45",
        "tqdm",
    ],
)
