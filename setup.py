from distutils.core import setup
setup(
  name = 'tfr2human',
  py_modules = ['tfr2human'],
  version = '0.0.0.1',
  description = 'Python Multiprocessing helpers',
  author = 'Brookie Guzder-Williams',
  author_email = 'brook.williams@gmail.com',
  url = 'https://github.com/brookisme/tfr2human',
  download_url = 'https://github.com/brookisme/tfr2human/tarball/0.1',
  keywords = ['TensorFlow','Tensor Flow Records','machine learning'],
  include_package_data=True,
  data_files=[
    (
      'config',[]
    )
  ],
  classifiers = [],
  entry_points={
      'console_scripts': [
      ]
  }
)