from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='archivy_hn',
    version='0.1.0',
    author="Uzay-G",
    author_email="halcyon@disroot.org",
    description=(
        "Archivy extension to sync upvoted posts from your hn account to your archivy instance."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    packages=find_packages(),
    entry_points='''
        [archivy.plugins]
        hn-sync=archivy_hn:hn_sync
    '''
)
