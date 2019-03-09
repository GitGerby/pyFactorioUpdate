#!/usr/bin/python3
'''
pyFactorioUpdate was created to eliminate the toil involved in updating a headless Factorio server.
When run the script will compare the last-modified header of the Factorio archive available for
download against the creation time of the most recently downloaded archive, if the web version
is newer it will be fetched and installed. Using -e or --experimental will compare against the
experimental version of Factorio rather than the stable version. To force a download and 
installation regardless of timestamps use -f or --force.
'''

import argparse as pr
import datetime as dt
import os
import shutil as sh
import tarfile as tf
import subprocess as sp
import requests as rq


def download_file(src, dest):
    '''
    downloads a file
    '''

    download = rq.get(src, stream=True)
    with open(dest, 'wb') as file_descriptor:
        for chunk in download.iter_content(chunk_size=128):
            file_descriptor.write(chunk)
    file_descriptor.close()
    download.close()
    print("downloaded {} to {}".format(src, dest))


def extract_factorio(archive, dest):
    '''
    extracts the downloaded tar
    '''
    archive = tf.open(archive)
    archive.extractall(dest)
    return TMP_STAGING + '/factorio/'


def get_latest_version(experimental):
    '''
    returns the datetime of the package available for download and the URL
    to retrieve that package
    '''
    if experimental:
        url = 'https://www.factorio.com/get-download/latest/headless/linux64'
    else:
        url = 'https://www.factorio.com/get-download/stable/headless/linux64'

    head = rq.head(url, allow_redirects=True)

    server_datestring = head.headers['Last-Modified']
    return (dt.datetime.strptime(server_datestring,
                                 '%a, %d %b %Y %H:%M:%S %Z'), url)


PARSER = pr.ArgumentParser()
PARSER.add_argument(
    '-e',
    '--experimental',
    help="Use Factorio's experimental track rather than stable",
    action='store_true')
PARSER.add_argument(
    '-f',
    '--force',
    help='Force download and extraction even if Factorio seems up to date',
    action='store_true')
PARSER.add_argument(
    '--tmp_dir',
    default='/tmp/factorio-updater/',
    help=
    'Temporary directory to use during processing, defaults to /tmp/factorio-updater/',
)
ARGS = PARSER.parse_args()

CURRENT_ARCHIVE = '/opt/factorio-updater/current'
if os.path.exists(CURRENT_ARCHIVE):
    CURRENT_ARCHIVE_TS = os.path.getctime(CURRENT_ARCHIVE)
    CURRENT_ARCHIVE_DATETIME = dt.datetime.fromtimestamp(CURRENT_ARCHIVE_TS)
else:
    print('Unable to determine timestamp of currently installed instance')
    CURRENT_ARCHIVE_DATETIME = dt.datetime.fromtimestamp(0)

TMP_DIR = ARGS.tmp_dir
TMP_FILE = TMP_DIR + 'archive.tar'
TMP_STAGING = TMP_DIR + '/staging/'

if not os.path.exists(TMP_DIR):
    print('creating temporary directory {}'.format(TMP_DIR))
    os.mkdir(TMP_DIR, 0o755)

if not os.path.exists(TMP_STAGING):
    print('creating staging folder {}'.format(TMP_STAGING))
    os.mkdir(TMP_STAGING, 0o755)

if os.path.exists(TMP_FILE):
    print('cleaning up old temp file')
    os.remove(TMP_FILE)

SERVER_DATETIME, URL = get_latest_version(ARGS.experimental)

if SERVER_DATETIME > CURRENT_ARCHIVE_DATETIME or ARGS.force:
    print('new version of Factorio detected, beginning download')
    download_file(URL, TMP_FILE)
    print('downloaded new version to {}'.format(TMP_FILE))

    NEW_FACTORIO = extract_factorio(TMP_FILE, TMP_STAGING)

    print('Stopping Factorio')
    return_code = sp.run(['systemctl', 'stop', 'factorio']).returncode
    if return_code != 0:
        raise RuntimeError
    print('Stopped Factorio')

    print('Copying new files')
    return_code = sp.run(['cp', '-R', NEW_FACTORIO, '/opt/']).returncode
    if return_code != 0:
        raise RuntimeError
    print('Copied new files')

    print('Starting Factorio')
    return_code = sp.run(['systemctl', 'start', 'factorio']).returncode
    if return_code != 0:
        raise RuntimeError
    print('Started Factorio')

    print('Updating current archive')
    sh.move(TMP_FILE, CURRENT_ARCHIVE)
else:
    print('Factorio is already up to date')

sh.rmtree(TMP_STAGING)
