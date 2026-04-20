PYTHON     := python/.venv/bin/python
BUILD_DIR  := analyzing/build

.PHONY: all setup setup-python setup-cpp run scrape analyze viz clean

all: run

# ── Setup ──────────────────────────────────────────────────────────────────

setup: setup-python setup-cpp
	@echo "Setup complete. Run 'make run' to start the pipeline."

setup-python: python/.venv/bin/python
python/.venv/bin/python:
	python3 -m venv python/.venv
	python/.venv/bin/pip install --quiet -r python/requirements.txt
	python/.venv/bin/playwright install chromium

setup-cpp: $(BUILD_DIR)/analyze
$(BUILD_DIR)/analyze: analyzing/CMakeLists.txt analyzing/analyze.cpp
	mkdir -p $(BUILD_DIR)
	cmake -S analyzing -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=Release
	cmake --build $(BUILD_DIR)

# ── Pipeline steps ─────────────────────────────────────────────────────────

scrape: setup-python
	$(PYTHON) python/scraping/fetch_balance.py

dev-scrape: setup-python
	$(PYTHON) python/scraping/fetch_balance_dev.py

analyze: setup-cpp
	$(BUILD_DIR)/analyze

viz: setup-python
	$(PYTHON) python/visualizing/vizualize.py

run: scrape analyze viz

# ── Cleanup ────────────────────────────────────────────────────────────────

clean:
	rm -rf $(BUILD_DIR)
	rm -f jsons/history.json jsons/balances.json jsons/rawHistory.json
	rm -f python/visualizing/*.png
