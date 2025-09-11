#!/usr/bin/env python3
"""
Setup script for FabricLA-Connector framework.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Microsoft Fabric Log Analytics Connector Framework"

# Read requirements from requirements.txt
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'azure-identity>=1.12.0',
        'azure-keyvault-secrets>=4.7.0',
        'azure-monitor-ingestion>=1.0.3',
        'requests>=2.28.0',
        'msal>=1.20.0',
        'python-dateutil>=2.8.0'
    ]

setup(
    name="fabricla-connector",
    version="1.0.0",
    author="Microsoft Fabric Monitoring Team",
    description="A comprehensive framework for collecting and ingesting Microsoft Fabric monitoring data",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=read_requirements(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    keywords="microsoft fabric monitoring azure log-analytics data-collection",
    project_urls={
        "Documentation": "https://github.com/your-org/fabric-la-connector",
        "Source": "https://github.com/your-org/fabric-la-connector",
        "Tracker": "https://github.com/your-org/fabric-la-connector/issues",
    },
    entry_points={
        'console_scripts': [
            'fabric-monitor=fabricla_connector.workflows:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
