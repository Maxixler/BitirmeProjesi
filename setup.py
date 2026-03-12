"""
USRP E310 & LoRaWAN & NOMA Sinyal Analiz Paketi - Kurulum Dosyasi
"""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", encoding="utf-8") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="usrp_noma",
    version="1.0.0",
    description="USRP E310 ile LoRaWAN Sinyal Analizi ve NOMA Coklu Erisim",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Bitirme Projesi",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "usrp-noma=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Communications :: Ham Radio",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)
