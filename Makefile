test:
	nosetests -v --with-coverage --cover-package=braspag

coverage:
	nosetests -v --with-coverage --cover-package=braspag --cover-html
	open cover/index.html

clean:
	rm -rf cover/
