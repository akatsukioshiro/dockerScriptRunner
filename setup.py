from setuptools import setup, Extension, find_packages

with open('README.md') as f:
	extd_desc = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
	# Meta information
	name				 = 'sample_name',
	version				 = '0.1.0',
	author				 = 'Ashish Nair',
	author_email		 = 'ashishnair.oph@gmail.com',
	url				     = 'https://github.com/akatsukioshiro/dockerScriptRunner',
	description			 = 'Automatic allocation of resources on a central group of resources for containerized execution of user tasks.',
	keywords			 = ['docker', 'scriptRunner', 'python'],
	install_requires	 = requirements,
	# build information
	py_modules			 = ['sample_name'],
	packages			 = find_packages(),
	package_dir			            = {'sample_name' : 'sample_name'},
	include_package_data            = True,
	long_description	            = extd_desc,
	long_description_content_type	= 'text/markdown',
	# package_data			= {'diweir' : [
	# 					'databank/*',
	# 					'datadump/*',
	# 					'factuals/*'
	# 					]},
    entry_points		= {'console_scripts' : ['diweir = diweir:run'],},
	zip_safe			= True,
	# https://stackoverflow.com/questions/14399534/reference-requirements-txt-for-the-install-requires-kwarg-in-setuptools-setup-py
	classifiers			= [
		"Programming Language :: Python :: 3",
		"Operating System :: OS Independent",
	],
	license 			= license
)
