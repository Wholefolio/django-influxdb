from setuptools import setup, find_packages


with open('README.md', 'r') as f:
    readme = f.read()


setup(name='django-influxdb',
      version='0.2.1',
      description='Django based InfluxDB manager',
      long_description=readme,
      long_description_content_type='text/markdown',
      url='http://gitlab.com/atkozhuharov/django-influxdb',
      author='Atanas K',
      author_email='atkozhuharov@gmail.com',
      license='MIT',
      install_requires=[
          'django>=2.2',
          'djangorestframework>3.0',
          'influxdb-client>=1.16'
      ],
      packages=find_packages())
