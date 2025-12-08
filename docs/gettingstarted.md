# Getting Started

Welcome to the VAMPIRES instrument control manual. Theis documentation serves as the primary resource for operating VAMPIRES and is composed of as much automatically-generated docs as possible so that it stays up to date with less direct maintenence. The version of these docs on the VAMPIRES computer will always serve as the most up-to-date reference for this manual.

## Navigating the Documentation

### Operating VAMPIRES

The operations documentation is mostly technical information-- how does VAMPIRES work, what are the interfaces with the hardware and cameras, etc. 

### Procedures

There are some tutorials for different operational aspects of VAMPIRES, like autofocusing and coronagraph alignment. These procedures are focused on accmoplishing tasks without explaining each technical component- for more information refere back to the operations documentation.

### Observing with VAMPIRES

These documents contain explicit checklists and procedures for observing with VAMPIRES. These steps may include references back to other procedures

## Code Examples

In general, if there are code examples they will come in these forms:

### 1. Python example

These examples will have python prompts `>>>` included in them. For example
```python
>>> dev = connect(VAMPIRES.FILTER)
```
### 2. Command line

Any command line program to run will come in the format
```
[computer] $ [prog]
```
for example
```
scexao5 $ cam-vcamstart
```
so that the computer you are running the command on is obvious. In the case that a command can run an _any_ computer, the command will look like
```
$ [prog]
```
for example
```
$ pgrep "dpp"
```

## How to edit the documentation

In case you find a mistake, ommission, or a new FAQ/troubleshooting item, the docs can be directly edited in markdown format with the `vampires_control/docs` directory of the source code. If a page already exists, it can be edited directly on GitHub using their built-in editor for [the repository](https://github.com/scexao-org/vampires_control/tree/main/docs). To build the documentation locally, make sure you've installed the optional documentation dependencies with
```
cd vampires_control/
pip install .[docs]
```
and then use Sphinx to build the documentation locally, one of the simpler ways is to use the `Makefile`

```
cd docs/
make html
```
which outputs to `vampires_control/docs/_build/html` and can be seen in a web browser at the URI `file:///home/lestat/src/vampires_control/docs/_build/html/index.html`. If you are doing many changes it is convenient to auto-build the docs and view them as an http server using the `sphinx-auto-build` package
```
cd vampires_control/
sphinx-auto-build docs docs/_build/html
```
which will spin up a local http server you can reach from `localhost` or forward over an SSH connection (i.e., VSCode remote does this automatically and you can view on YOUR host machine's browser).

Once your changes are ready, commit and push them to GitHub using git, and the online documentation should build and update within a few minutes using GitHub actions.
