# 240_final_project

Scrapes University of Richmond One Card spending history, processes it with C++,
and visualizes balance and daily spending over time.

## Requirements

- Python 3 + `make`
- CMake 3.14+ and a C++17 compiler (install via `brew install cmake`)

## Setup (one time)

```
make setup
```

This creates a Python virtual environment, installs all dependencies,
installs the Playwright Chromium browser, and compiles the C++ analyzer.

## Run the pipeline

```
make run
```

Steps in order:
1. **Scrape** — launches Chromium, logs in to `onecardweb.richmond.edu`, and writes `jsons/rawHistory.json`
2. **Analyze** — C++ binary parses the JSON and writes `jsons/history.json`
3. **Visualize** — Python reads the processed data and saves PNGs to `python/visualizing/`

## Individual steps

```
make scrape    # step 1 only
make analyze   # step 2 only
make viz       # step 3 only
```

## Clean up generated files

```
make clean
```
