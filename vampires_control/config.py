import os

DEVICE_ADDRESSES_FILE = os.environ.get(
    "VAMPIRES_DEVICE_ADDRESSES", "/etc/vampires_control/device_addresses.json"
)
QWP_OFFSETS_FILE = os.environ.get(
    "VAMPIRES_QWP_OFFSETS", "/etc/vampires_control/conf_qwp.json"
)
