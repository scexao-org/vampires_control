VAMPIRES Instrument Manual
==========================

.. image:: https://img.shields.io/badge/Code-GitHub-black.svg
   :target: https://github.com/scexao-org/vampires_control
.. image:: https://github.com/scexao-org/vampires_control/actions/workflows/CI.yml/badge.svg?branch=main
   :target: https://github.com/scexao-org/vampires_control/actions/workflows/CI.yml
.. image:: https://codecov.io/gh/scexao-org/vampires_control/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/scexao-org/vampires_control
.. image:: https://img.shields.io/github/license/scexao-org/vampires_control?color=yellow
   :target: https://github.com/scexao-org/vampires_control/blob/main/LICENSE

**Primary maintainer:** `Miles Lucas <https://github.com/mileslucas>`_ (mdlucas@hawaii.edu)

Welcome to the instrument manual and documentation for SCExAO/VAMPIRES. This documentation is a mix of technical instrument information, API documentation, procedures, and checklists. The documentation is built directly into the python package ``vampires_control``, which is used for the VAMPIRES instrument control. Other important code repositories include ``device_control`` (hardware interfaces), ``swmain`` (SCExAO common tools), and others (TODO).

.. admonition:: Warning: 🧪 Experimental and 🚧 Under Construction
   :class: warning

   ``vampires_control`` is still under development, and the API can change without notice. Use with your own caution (and consider contributing).


Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   installation
   gettingstarted
   api/index

.. toctree::
   :maxdepth: 1
   :caption: Operating VAMPIRES

   operating/layout
   operating/cameras
   operating/viewers
   operating/coronagraphs
   operating/devices
   operating/data
   operating/troubleshooting

.. toctree::
   :maxdepth: 1
   :caption: Procedures

   procedures/autofocus
   procedures/coronagraphs
   procedures/mbi

.. toctree::
   :maxdepth: 1
   :caption: Observing with VAMPIRES

   observing/calibrations
   observing/polarimetry
   observing/data


License
-------

``vampires_control`` is licensed under the MIT open-source license. See `LICENSE <https://github.com/scexao-org/vampires_control/blob/main/LICENSE>`_ for more details.


Contributing and Support
------------------------

If you would like to contribute, feel free to open a `pull request <https://github.com/scexao-org/vampires_control/pulls>`_. If you're having problems with something, please open an `issue <https://github.com/scexao-org/vampires_control/issues>`_.


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`