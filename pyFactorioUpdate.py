import requests as rq
import datetime as dt
import os as os
import argparse as pr

parser = pr.ArgumentParser()
parser.add_argument('-e','--experimental',help="Use Factorio's experimental track rather than stable",action='store_true')
args = parser.parse_args()

current_archive = '/opt/factorio-updater/current'
current_archive_date = os.path.getctime(current_archive)

if args.experimental:
  url = 'https://www.factorio.com/get-download/latest/headless/linux64'
else:
  url = 'https://www.factorio.com/get-download/stable/headless/linux64'

head = rq.head(url, allow_redirects=True)
head.close()

server_datestring = head.headers['Last-Modified']
server_datetime = dt.datetime.strptime(server_datestring, '%a, %d %b %Y %H:%M:%S %Z')


if server_datetime > current_archive_date:
  