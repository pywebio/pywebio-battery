import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'pywebio_battery', '__version__.py'), encoding='utf8') as f:
    exec(f.read(), about)

with open('README.md', encoding='utf8') as f:
    readme = f.read()


setup(
    name=about['__package__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    license=about['__license__'],
    python_requires=">=3.5.2",
    packages=['pywebio_battery'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
        'pywebio',
    ],
    project_urls={
        'Documentation': about['__url__'],
        'Source': 'https://github.com/wang0618/pywebio-battery',
    },
)
