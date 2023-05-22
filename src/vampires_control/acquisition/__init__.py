import logging

# set up logging
_formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("data_acquisition")
logger.setLevel(logging.INFO)
_stream_handler = logging.StreamHandler()
_stream_handler.setLevel(logging.INFO)
_stream_handler.setFormatter(_formatter)
logger.addHandler(_stream_handler)