PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test run clean

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) -m depgraph $(ARGS)

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -f graph.png
