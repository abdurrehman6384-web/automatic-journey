PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install test demo mcp-tools devices vendor clean

help:
	@echo "make install    create .venv and install requirements"
	@echo "make test       run the full suite (62 tests, no phone needed)"
	@echo "make demo       run the full-control demo against a fake device"
	@echo "make mcp-tools  list the MCP tools the server exposes"
	@echo "make devices    show what adb currently sees"
	@echo "make vendor     clone the uiautomator2 + lamda reference repos"

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

test:
	$(PY) -m pytest tests/ -q

demo:
	$(PY) examples/full_control_demo.py --dry-run

mcp-tools:
	$(PY) mcp_server.py --list

devices:
	$(PY) -c "from androidctl import list_devices; \
		[print(f'{d.serial:28s} {d.state:12s} {d.model}') for d in list_devices()] \
		or print('no devices')"

vendor:
	mkdir -p vendor && cd vendor && \
	git clone --depth 1 https://github.com/openatx/uiautomator2.git || true && \
	git clone --depth 1 https://github.com/firerpa/lamda.git || true

clean:
	rm -rf .pytest_cache **/__pycache__ examples/output
