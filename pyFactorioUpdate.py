#!/usr/bin/python3
'''
pyFactorioUpdate was created to eliminate the toil involved in updating a headless Factorio server
'''

import argparse as pr
import datetime as dt
import os
import shutil as sh
import tarfile as tf
import requests as rq

def download_file(src, dest):
    '''
    downloads a file
    '''
    
    r = rq.get(src, stream=True)
    with open(dest, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    fd.close()
    print("downloaded {} to {}".format(src, dest))

parser = pr.ArgumentParser()
parser.add_argument('-e', '--experimental', help="Use Factorio's experimental track rather than stable", action='store_true')
parser.add_argument('-f', '--force', help='Force download and extraction even if Factorio seems up to date', action='store_true')
ARGS = parser.parse_args()

current_archive = '/opt/factorio-updater/current'
current_archive_ts = os.path.getctime(current_archive)
current_archive_datetime = dt.datetime.fromtimestamp(current_archive_ts)

tmp_dir = '/tmp/factorio-updater/'
tmp_filename = 'archive.tmp'
tmp_file = tmp_dir + tmp_filename
tmp_staging = '/tmp/factorio-updater/staging/'

if not os.path.exists(tmp_dir):
    print('creating temporary directory {}'.format(tmp_dir))
    os.mkdir(tmp_dir,0o755)

if not os.path.exists(tmp_staging):
    print('creating staging folder {}'.format(tmp_staging))
    os.mkdir(tmp_staging,0o755)

if os.path.exists(tmp_file):
    print('cleaning up old temp file')
    os.remove(tmp_file)


if ARGS.experimental:
    url = 'https://www.factorio.com/get-download/latest/headless/linux64'
else:
    url = 'https://www.factorio.com/get-download/stable/headless/linux64'

head = rq.head(url, allow_redirects=True)

server_datestring = head.headers['Last-Modified']
server_datetime = dt.datetime.strptime(server_datestring, '%a, %d %b %Y %H:%M:%S %Z')


if server_datetime > current_archive_datetime or ARGS.force:
    print('new version of Factorio detected, beginning download')
    download_file(url, tmp_file)
    print ('downloaded new version to {}'.format(tmp_file))
    archive = tf.open(tmp_file)
    archive.extractall(tmp_staging)
else:
    print('Factorio is already up to date')

sh.rmtree(tmp_dir)
