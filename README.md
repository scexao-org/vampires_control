# VAMPIRES control

[![CI tests](https://github.com/scexao-org/vampires_control/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/scexao-org/vampires_control/actions/workflows/CI.yml)
[![Docs](https://github.com/scexao-org/vampires_control/actions/workflows/docs.yml/badge.svg?branch=main)](https://scexao-org.github.io/vampires_control)
[![Coverage](https://codecov.io/gh/scexao-org/vampires_control/branch/main/graph/badge.svg)](https://codecov.io/gh/scexao-org/vampires_control)
[![License](https://img.shields.io/github/license/scexao-org/vampires_control?color=yellow)](LICENSE)

**WARNING:** Work in progress

Maintainer: [Miles Lucas](https://github.com/mileslucas)

## Installation

This software relies on [scxkw](https://github.com/scexao-org/SCeXaoKeyWords), please follow the installation instructions there before installing this code.

```
$ git clone https://github.com/scexao-org/vampires_control
$ pip install [-e] vampires_control
```

then, copy the configuration files to the appropriate directory

```
$ mkdir /etc/vampires_control
$ cp vampires_control/conf/* /etc/vampires_control/
```
or, if you prefer symlinks
```
$ ln -s vampires_control/conf/* /etc/vampires_control/
```

## Configuration

The configuration files are all stored in TOML format. `/etc/vampires_control`.

## Status

## Scripts

* `vampires_qwp_daemon`
* `vampires_temp_daemon`