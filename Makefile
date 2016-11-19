install:
	pyvenv env
	. env/bin/activate
	pip install flask
	pip install arrow
	pip install pymongo
