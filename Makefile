test:
	python3 ./runtests.py

release:
	python3 setup.py sdist
	twine upload dist/*
