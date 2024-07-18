import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyterrier-alpha",
    version="0.3.0",
    author="Sean MacAvaney",
    author_email='sean.macavaney@glasgow.ac.uk',
    description="Alpha channel of features for PyTerrier",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
      'python-terrier',
    ],
    extras_require = {
        'java': ["pyjnius>=1.4.2"],
    },
    entry_points={
        'pyterrier.java.init': [
            'pyterrier-alpha:java._legacy_init',
        ],
    },
    python_requires='>=3.6',
)
