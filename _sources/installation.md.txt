# Installation


`vampires_control` requires at least python 3.7

## Using `pip`

For now, install directly from GitHub

```bash
$ pip install -U git+https://github.com/scexao-org/vampires_control.git#egg=vampires_control
```

This will install the required dependencies.


## From Source

The source code for `vampires_control` can be downloaded and installed [from GitHub](https://github.com/scexao-org/vampires_control) by running

```bash
$ git clone https://github.com/scexao-org/vampires_control
$ cd vampires_control
$ pip install .
```

## Testing

To run the unit tests, install the development dependencies using pip:

```bash
$ pip install ".[test]"
```

and then execute:

```bash
$ python -m pytest
```

This will automatically run the tests with plugins enabled. All of the tests should (of course) pass. If any of the tests don't pass and if
you can't sort out why, [open an issue on GitHub](https://github.com/scexao-org/vampires_control/issues).


```{admonition} Debugging tests in VS code
:class: tip
    
The default pytest configuration runs with coverage, which disables certain python debugging environments, like in VS code. To fix this, add::

    "python.testing.pytestArgs": ["tests", "--no-cov"]

to ``settings.json`` either globally or locally.
```
