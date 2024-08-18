import setuptools

def get_version(path):
    for line in open(path, 'rt'):
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setuptools.setup(
    name="pyterrier-alpha",
    version=get_version("pyterrier_alpha/__init__.py"),
    author="Sean MacAvaney",
    author_email='sean.macavaney@glasgow.ac.uk',
    description="Alpha channel of features for PyTerrier",
    long_description=open('README.md', 'rt').read(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
      'python-terrier',
    ],
    entry_points={
        'pyterrier.artifact.url_protocol_resolver': [
            'hf = pyterrier_alpha.artifact:_hf_url_resolver',
        ]
    },
    python_requires='>=3.6',
)
