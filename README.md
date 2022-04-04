# VAMPIRES control

**WARNING:** Work in progress

Maintainer: [Miles Lucas](https://github.com/mileslucas)

## Installation

This software relies on [scxkw](https://github.com/scexao-org/SCeXaoKeyWords), please follow the installation instructions there before installing this code.

```
$ git clone https://github.com/scexao-org/vampires_control
$ pip install vampires_control [-e]
```

then, copy the configuration files to the appropriate directory

```
$ mkdir /etc/vampires_control
$ cp vampires_control/conf/* /etc/vampires_control/
```

## Configuration

The configuration files are all stored in JSON format for crystal-clear hierarchical storage. I recommend using [jq](https://stedolan.github.io/jq/) for quick viewing and editing of the files when stored in `/etc/vampires_control`.

For example, let's say you wanted to change the default conex angle for one of the pupil wheel positions- in this case we want to put the Lyot stop at 192.6 degrees. This is mask number 9, so the index in the configuration array is 8 (JSON is 0-indexed).

```
$ jq ".positions[8].angle" /etc/vampires_control/conf_pupil_wheel.json
192.5
$ jq ".positions[8].angle |= 192.6" /etc/vampires_control/conf_pupil_wheel.json > /etc/vampires_control/conf_pupil_wheel.json
$ jq ".positions[8].angle" /etc/vampires_control/conf_pupil_wheel.json
192.6
```

you can use this to quickly see data in "columns"

```
$ jq ".positions[] | .name, .angle" /etc/vampires_control/conf_beamsplitter.json
"Open"
0
"Polarizer"
45
"Open"
90
"700 SP"
133.95
"Open"
180
"50/50"
224.65
"Open"
270
"750 SP"
315
```

## Status

The state, as managed by `vampires_control.state.VAMPIRES`, is saved locally to a JSON file at `/etc/vampires_control/vampires_state.json` and pushed updates to the redis database managed on `scexao3` (warnings are thrown for missing keys, but no errors). You can use the `vampires_status` script to print the whole status, or a single key, or you can use `jq` to directly query the JSON file-

```
$ jq . /etc/vampires_control/vampires_state.json
{
  "beamsplitter": "6",
  "beamsplitter_status": "50/50",
  "beamsplitter_angle": 224.6502,
  "diffwheel": "2",
  "diffwheel_status": "Open / Open",
  "diffwheel_cam1": "Open",
  "diffwheel_cam2": "Open",
  "diffwheel_angle": 45,
  "focus_stage": 16,
  "pupil_wheel": "1",
  "pupil_wheel_status": "Open",
  "pupil_wheel_angle": 0,
  "pupil_wheel_x": 188000,
  "pupil_wheel_y": 121000,
  "qwp_1": 128,
  "qwp_2": 168
}
```

## Scripts

* `vampires_beamsplitter`
* `vampires_diffwheel`
* `vampires_focus`
* `vampires_pupil`
* `vampires_qwp`
* `vampires_status`

**DEPRECATIONS:**
* `conex`
