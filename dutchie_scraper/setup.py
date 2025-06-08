from setuptools import setup, find_packages

setup(
    name='dutchie_scraper',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A package to scrape product data from Dutchie-based websites.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/dutchie_scraper',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'selenium',
        'pandas',
        'flask',
        'flask-pymongo',
        'webdriver-manager',
        'selenium-stealth',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)