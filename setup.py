from setuptools import setup

MAINTAINER_EMAIL = 'tanguy.lunel.1@ens.etsmtl.ca'
AUTHORS = 'Tanguy LUNEL'

setup(
   name='pvpumpingsystem',
   version='0.9',
   description=('Module for simulating off-grid photovoltaic powered '
                'pumping station'),
   license='GPL3',
   author=AUTHORS,
   author_email=MAINTAINER_EMAIL,
   url='https://github.com/tylunel/pvpumpingsystem',
   packages=['pvpumpingsystem'],  # same as name
   # external dependencies packages
   install_requires=['pvlib==0.10.1',
                     'fluids', 
                     'numpy-financial',
                     'matplotlib',
                     'pytest',
                     'scikit-learn',
                     'tqdm',
                     'setuptools'],
   package_data={
       'pvpumpingsystem': ['data/pump_files/*.txt'],
   }
   )
