from setuptools import setup, find_packages

setup(
    name='firebatch',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click>=8.0.0',
        'google-cloud-firestore>=2.1.0',
    ],
    extras_require={
        'validation': ['pydantic>=1.8.2']
    },
    entry_points={
        'console_scripts': [
            'firebatch = firebatch.cli:cli',
        ],
    },
)
