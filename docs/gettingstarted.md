# Getting Started

Welcome to the VAMPIRES instrument control manual. Theis documentation serves as the primary resource for operating VAMPIRES and is composed of as much automatically-generated docs as possible so that it stays up to date with less direct maintenence. The version of these docs on the VAMPIRES computer will always serve as the most up-to-date reference for this manual.

## Navigating the Documentation

Each major section of operating VAMPIRES is broken into 

1. Camera operation
2. Device control
3. Data acquisition
4. Calibrations

In addition, there are some full tutorials for these observational modes of VAMPIRES
1. Single-cam imaging
2. Polarimetric imaging
3. Narrowband / SDI imaging
4. Sparse Aperture Mask interferometry

Finally, there are miscellaneous documentation for servicing VAMPIRES, mostly technical information for people working on the bench
1. Aligment and Baffling
2. Cameras
3. Parts and Design

## Code Examples

In general, if there are code examples they will come in these forms:

1. **Python example**

These examples will have python prompts `>>>` included in them. For example
```python
>>> dev = connect(VAMPIRES.FILTER)
```
2. **Command line**

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

## FAQ

Each section of the documentation contains a frequently asked questions (FAQ) page to hopefully answer your questions about VAMPIRES. If there's something that slipped through the cracks, reach out on the SCExAO slack `#bench_help` channel, or email me directly (Miles Lucas <mdlucas@hawaii.edu>). Please be considerate of the SCExAO team's time and double-check the documentation (use the search bar!) before reaching out.
