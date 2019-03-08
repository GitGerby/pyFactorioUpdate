#!/usr/bin/python3
import requests as rq
import datetime as dt
import os as os
import argparse as pr
import tarfile as tf

def download_file(url,dest_dir,dest_file):
  r = rq.get(url, stream=True)
  with open(dest_dir + dest_file, 'wb') as fd:
    for chunk in r.iter_content(chunk_size=128):
      fd.write(chunk)
  fd.close()
  print "downloaded {url} to {dest}".format(url,dest_dir + dest_file)

parser = pr.ArgumentParser()
parser.add_argument('-e', '--experimental', help="Use Factorio's experimental track rather than stable", action='store_true')
args = parser.parse_args()

current_archive = '/opt/factorio-updater/current'
current_archive_ts = os.path.getctime(current_archive)
current_archive_datetime = dt.datetime.fromtimestamp(current_archive_ts)

tmp_dir = '/tmp/factorio-updater'
tmp_file = 'archive.tmp'
tmp_staging = '/tmp/factorio-updater/staging'

if not os.path.exists(tmp_dir):
  print('creating temporary directory {}'.format(tmp_dir))
  os.mkdir(tmp_dir,0o755)

if not os.path.exists(tmp_staging):
  print('creating staging folder {}'.format(tmp_staging))
  os.mkdir(tmp_staging,0o755)

if os.path.exists(tmp_file):
  print('cleaning up old temp file')
  os.remove(tmp_file)


if args.experimental:
  url = 'https://www.factorio.com/get-download/latest/headless/linux64'
else:
  url = 'https://www.factorio.com/get-download/stable/headless/linux64'

head = rq.head(url, allow_redirects=True)

server_datestring = head.headers['Last-Modified']
server_datetime = dt.datetime.strptime(server_datestring, '%a, %d %b %Y %H:%M:%S %Z')


if server_datetime > current_archive_datetime:
  print('new version of Factorio detected, beginning download')
  download_file(url, tmp_dir, tmp_file)
  print ('downloaded new version to {}'.format(tmp_file))
else:
  print('Factorio is already up to date')

os.remove(tmp_dir)