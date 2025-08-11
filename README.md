## Dev setup

### Mac:

1. Install homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
1. Install python 3.12: `brew install python@3.12`
1. Create .venv: `python3.12 -m venv .venv`
1. Activate .venv: `source .venv/bin/activate`
1. Upgrade pip: `pip install --upgrade pip`
1. Install depedendencies: `python3 -m pip install -r requirements.txt`
1. [Install or update Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#install-or-update-core-tools)
