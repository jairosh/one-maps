# one-maps
Tools and scripts necessary to create scenarios for The ONE based in OpenStreetMaps data

# Installation and usage

## Using poetry
This project uses poetry for dependency management, using it is straightforward:

```shell
$ poetry install
$ poetry shell
# Run the scripts with python NAME_OF_SCRIPT
```

## Using venv
Alternatively, there's a requirements.txt included for those that can't/want use poetry and instead want to use a virtualenv:

```shell
# Create a virtualenv
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
# Run the scripts with python NAME_OF_SCRIPT
```