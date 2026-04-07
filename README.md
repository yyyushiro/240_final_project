# 240_final_project

# Environments(complicated)
## Start

```
git clone https://github.com/yyyushiro/240_final_project.git
cd 240_final_project
```
## Python(`scraping`)
The code below is for making a virtual environment and installing necessary libraries.
```
cd scraping
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```
- make .env file contains `USERNAME` and `PASSWORD`(e.g. `USERNAME = ymurakami`, `PASSWORD = richmond`)
- execution: `python fetch_balance.py`
- The place of `out.json`: `/scraping`

## C++(`analyzing`)
The code below is for compiling the C++ files in analyzing.
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" <- If you do not have homebrew
brew install cmake <- If you do not have cmake
cd analyzing
mkdir -p build && cd build
cmake ..                 
cmake --build .
./analyze ../scraping/out.json   
```

## How to use (for dev)
1. Create .env file in `./python/scraping` and set your `USERNAME` and `PASSWORD`.
   This program never saves any of your information, but if you feel threathen, then you can choose login manually + scraping.
2. Run a python file in scraping. If you made .env file, then enter "Y" in the terminal. If not, log in, then enter "n" in the terminal. You will get the json file with your spending history.
3. Run a C++ file in analizing. You will get the json file with your processed spending history(for now, it's just parsing the dollars into float).
4. Run a python file in vizualizing. You will get the vizualized image of the spending history.