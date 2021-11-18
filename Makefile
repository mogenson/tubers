run: build
	python -m http.server -d public/

build: clean
	mkdir -p public
	cp index.html public/
	python -m compileall -f -b app
	zip -r public/app.zip app -i '*.pyc'
	find app -type f -name '*.pyc' -delete

clean:
	rm -rf public/

lint:
	black app/
	isort app/
