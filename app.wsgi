import sys
import site
import os

site.addsitedir('/var/www/marcus/env/lib/python3.13/site-packages')

sys.path.insert(0, '/var/www/marcus')

os.chdir('/var/www/marcus')

os.environ['VIRTUAL_ENV'] = '/var/www/marcus/env'
os.environ['PATH'] = '/var/www/marcus/env/bin:' + os.environ['PATH']

from app import app as application
