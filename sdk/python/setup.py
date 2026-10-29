from setuptools import setup, find_packages

setup(
    name="devalert-python",
    version="1.0.0",
    description="Universal Error Monitoring and Automated Developer Reporting Python SDK",
    author="DevAlert Team",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
