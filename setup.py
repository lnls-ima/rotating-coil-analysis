
from setuptools import setup

setup(
    name='rotcoilanalysis',
    version='0.1.1',
    description='Rotating Coil Package',
    url='https://github.com/lnls-ima/rotating-coil-analysis',
    author='lnls-ima',
    license='MIT License',
    packages=['rotcoilanalysis'],
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'reportlab',
    ],
    entry_points={
        'console_scripts': [
            'rotating-coil-analysis=rotcoilanalysis.rotcoilapp:run'
        ],
     },
    zip_safe=False)
