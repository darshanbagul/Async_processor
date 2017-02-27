import json
import os
from logging.config import dictConfig
import logging

path = 'logging.json'
if os.path.exists(path):
    with open(path, 'rt') as f:
        config = json.load(f)
    dictConfig(config)
else:
    logging.basicConfig(level=default_level)

logger = logging.getLogger()

