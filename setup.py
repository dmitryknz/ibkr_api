from setuptools import setup, find_packages

setup(
    name="ibkr_trading_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "ibapi>=9.81.1",
        "wxPython>=4.2.0",
        "pytz",
    ],
) 