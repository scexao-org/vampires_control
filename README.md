# VAMPIRES control

**WARNING:** Work in progress

Maintainer: [Miles Lucas](https://github.com/mileslucas)

## Installation

This software relies on [scxkw](https://github.com/scexao-org/SCeXaoKeyWords), please follow the installation instructions there before installing this code.

```
$ git clone https://github.com/scexao-org/vampires-control
$ pip install vampires-control [-e]
```

then, copy the configuration files to the appropriate directory

```
$ mkdir /etc/vampires-control
$ cp vampires-control/conf/* /etc/vampires-control/
```

## Configuration

The configuration files are all stored in JSON format for crystal-clear hierarchical storage. I recommend using [jq](https://stedolan.github.io/jq/) for quick viewing and editing of the files when stored in `/etc/vampires-control`.
