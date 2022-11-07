install-lib:
	rm -rf dist
	pip3 install wheel
	pip3 install setuptools
	pip3 install twine
	python setup.py bdist_wheel
	pip3 install --force-reinstall  dist/**.whl

tests:
	python -m unittest discover

lint:
	black .
	flake8 --max-line-length=88 bot --show-source --exit-zero --ignore=NF001

types:
	pytype --keep-going bot

run:
	streamlit run Homepage.py
