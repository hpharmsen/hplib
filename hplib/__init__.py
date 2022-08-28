import sys
assert sys.version_info >= (3,7), "To use hplib (an thus this script) you need to run Python 3.7 or newer"

from .dbclass import dbClass
from .mailclass import emailMessage, smtpServer