# python-poetry

A template project for a modern python script / tool with pretty logs and other development goodies

## Powered by
- [Python](https://www.python.org/) >= 3.6
- [Poetry](https://python-poetry.org/) for dependency management
- [Taskipy](https://github.com/illBeRoy/taskipy) for npm-style script commands

## Development notes

The application entry point is the `__main__.py` file inside the `application` folder (package). This way, the user can execute the script by simply running `python application`.

During development, you can also start the script with a taskipy task by running `poetry run task start`.

The Black formatter is included in the devdependencies - when using Visual Studio Code, you can format the code by pressing `Shift+Alt+F`. Make sure that Black is selected as Python's formatting provider in the extension settings.

The application starts by parsing the command line arguments with `argparse`, then sets up logging (with colors using [colorama](https://github.com/tartley/colorama) if possible), then runs the logic. `KeyboardInterrupts` can be used to stopped the application and are handled gracefully.

A `requirements.txt` file for the required dependencies can be exported from the poetry configuration by running `poetry run task freeze`.

You can instruct the end-users to install the required dependencies by running
- `poetry install --no-dev` if [Poetry](https://python-poetry.org/) is installed
- `pip install -r requirements.txt` otherwise