PYTHON ?= python3
LUA ?= lua
LUAC ?= luac
LUACHECK ?= luacheck

.PHONY: doctor install-dev install-release test test-python test-lua lint lint-python lint-lua \
	lua-syntax version-check docs-check demo readme-preview package package-plugin \
	package-engine package-wheel

doctor:
	$(PYTHON) scripts/dev.py doctor

install-dev:
	$(PYTHON) -m pip install -e './backend[dev]'

install-release:
	$(PYTHON) -m pip install -e './backend[release]'

test: test-python test-lua

test-python:
	PYTHONPATH=backend/src $(PYTHON) -m pytest backend/tests

test-lua:
	$(LUA) tests/lua/test_json.lua
	$(LUA) tests/lua/test_develop_settings.lua
	$(LUA) tests/lua/test_plugin_load.lua
	$(LUA) tests/lua/test_engine_client.lua
	$(LUA) tests/lua/test_workflow.lua

lint: lint-python lint-lua lua-syntax version-check docs-check

lint-python:
	$(PYTHON) -m ruff check backend scripts
	$(PYTHON) -m ruff format --check backend scripts

lint-lua:
	$(LUACHECK) plugin/Chameleon.lrplugin tests/lua

lua-syntax:
	find plugin/Chameleon.lrplugin tests/lua -name '*.lua' -print0 | xargs -0 -n1 $(LUAC) -p

version-check:
	$(PYTHON) scripts/sync_version.py --check

docs-check:
	$(PYTHON) scripts/check_docs.py

demo:
	PYTHONPATH=backend/src $(PYTHON) -m chameleon_engine demo --output-dir demo/output --force

readme-preview:
	$(PYTHON) scripts/render_readme_preview.py

package: package-plugin package-engine

package-plugin:
	$(PYTHON) scripts/package_plugin.py --output-dir dist

package-engine:
	$(PYTHON) scripts/build_engine.py --output-dir dist

package-wheel:
	$(PYTHON) -m pip wheel --no-deps ./backend --wheel-dir dist
