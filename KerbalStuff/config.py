import logging
from distutils.util import strtobool

try:
    from configparser import ConfigParser
except ImportError:
    # Python 2 support
    from ConfigParser import ConfigParser

# Load the software configuration
config = ConfigParser()
config.readfp(open('config.ini'))
env = 'dev'

_cfg = lambda k: config.get(env, k)
_cfgi = lambda k: int(_cfg(k))
_cfgb = lambda k: strtobool(_cfg(k)) == 1

logger = logging.getLogger(_cfg('site-name'))
logger.setLevel(logging.DEBUG)

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)

logger.addHandler(sh)

# scss logger
logging.getLogger("scss").addHandler(sh)

