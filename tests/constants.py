from os import getenv
from pathlib import Path


SERVER = "mail.gandi.net"
USER = "mickael@jmsinfo.co"
PASSWORD = getenv("MICKAEL_JMSINFO_CO_PWD")
FILE = Path(__file__).parent / "data" / "rules.ini"
