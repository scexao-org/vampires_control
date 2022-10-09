# Installation

```{margin}
`vampires_control` requires at least python 3.7
```

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
$ pip install .[test]
```

and then execute:

```bash
$ python -m pytest
```

This will automatically run the tests with plugins enabled. All of the tests should (of course) pass. If any of the tests don't pass and if
you can't sort out why, [open an issue on GitHub](https://github.com/scexao-org/vampires_control/issues).


```{eval-rst}
.. admonition:: Debugging tests in VS code
    :class: tip
    
    The default pytest configuration runs with coverage, which disables certain python debugging environments, like in VS code. To fix this, add::
    
        "python.testing.pytestArgs": ["tests", "--no-cov"]
    
    to ``settings.json`` either globally or locally.
```

## Advanced: Daemon Services

On the computer that is connected to the VAMPIRES hardware devices the many daemon services need to be set up and installed beyond what can be achieved with `pip`. One of the core building blocks of this control software is a series of daemons that have our 0MQ socket endpoints listening, waiting for tcp requests to control the hardware. These daemons can be started directly from python with

```bash
$ python -m vampires_control.daemons.<daemon>
```

for example, the daemon controlling the linear motor stage is `focus_daemon`

```bash
$ python -m vampires_control.daemons.focus_daemon
```

You'll notice that nothing appears to happen- this is because the daemons fork into a separate background process. To kill this process, find the corresponding PID in `top` and `SIGTERM` the process.

A series of `systemd` service files are in this repository for reliable and robust daemon deployment. At the top level there is a `vampiresd.service` which acts as a dummy to spawn and control all of the subsequent daemons. The full architecture is as follows-

`vampiresd.service`
* `focus_daemon.service`

### Installing the Daemon Services

To use these services, two steps need to be taken. First, the files in `conf/services` need to be copied to `/etc/systemd/user` (or [one of these other locations](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#User%20Unit%20Search%20Path))

```bash
$ sudo cp conf/services/*.service /etc/systemd/user/
```

Once those files are copied, we can use the `systemd` suite of tools for controlling the daemons. First, let's update the unit list and make sure the services are installed properly

```bash
$ systemctl daemon-reload
$ systemctl list-unit-files | grep vampires
```

you should see a list of services that looks like

```
vampiresd.service
vampires_focus_daemon.service
```

### Controlling the Daemons

to start all the daemons, use the `vampiresd` service

```bash
$ systemctl start vampiresd
```

to start or disable individual services

```bash
$ systemctl stop vampires_focus_dameon
$ systemctl start vampires_focus_daemon
```

to enable or disable launching on machine start

```bash
$ systemctl enable vampiresd
$ systemctl disable vampiresd
```

to remove a specific service from the `vampiresd` architecture so that restarting `vampiresd` does not restart this service

```{eval-rst}
.. admonition ::    
    :class: warning
    
    This will only change the behavior until the next machine restart, at which case the `enable`/`disable` behavior will take precedent
```

```bash
$ systemctl mask vampries_focus_daemon
$ systemctl unmask vampries_focus_daemon
```