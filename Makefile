setup:
	python3.12 -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python manage.py test