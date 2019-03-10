#!/usr/bin/python3
'''
pyFactorioUpdate was created to eliminate the toil involved in updating a headless Factorio server.
When run the script will compare the last-modified header of the Factorio archive available for
download against the creation time of the most recently downloaded archive, if the web version
is newer it will be fetched and installed. Using -e or --experimental will compare against the
experimental version of Factorio rather than the stable version. To force a download and
installation regardless of timestamps use -f or --force.
'''

import argparse
from datetime import datetime
import os
import shutil
import tarfile
import subprocess
import requests


def download_file(src, dest):
    '''Downloads a file.'''
    download = requests.get(src, stream=True)
    with open(dest, 'wb') as file_descriptor:
        for chunk in download.iter_content(chunk_size=128):
            file_descriptor.write(chunk)
    file_descriptor.close()
    download.close()
    print("Downloaded {} to {}".format(src, dest))


def extract_factorio(archive, dest):
    '''Extracts the downloaded tar.'''
    archive = tarfile.open(archive)
    archive.extractall(dest)
    return os.path.join(dest, 'factorio')


def get_latest_version(experimental):
    '''Returns the datetime of the package available for download and the URL
       to retrieve that package.
    '''
    url = 'https://www.factorio.com/get-download/{revision}/headless/linux64'.format(
        revision="latest" if experimental else "stable")
    response = rq.head(url, allow_redirects=True)
    return (datetime.strptime(response.headers['Last-Modified'],
                              '%a, %d %b %Y %H:%M:%S %Z'), url)

PARSER = argparse.ArgumentParser()
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
PARSER.add_argument(
    '--check_only',
    help=
    ('Only check whether there is a newer version available, do not fetch and install.',
     'Exits with 0 if no new package availble, 10 if newer version available.'),
    action='store_true')
ARGS = PARSER.parse_args()

CURRENT_ARCHIVE = '/opt/factorio-updater/current'
if os.path.exists(CURRENT_ARCHIVE):
    CURRENT_ARCHIVE_TS = os.path.getctime(CURRENT_ARCHIVE)
    CURRENT_ARCHIVE_DATETIME = datetime.fromtimestamp(CURRENT_ARCHIVE_TS)
else:
    print('Unable to determine timestamp of currently installed instance')
    CURRENT_ARCHIVE_DATETIME = datetime.fromtimestamp(0)

TMP_DIR = ARGS.tmp_dir
TMP_FILE = os.path.join(TMP_DIR, 'archive.tar')
TMP_STAGING = os.path.join(TMP_DIR, 'staging')

if not os.path.exists(TMP_DIR):
    print('Creating temporary directory {}.'.format(TMP_DIR))
    os.mkdir(TMP_DIR, 0o755)

if os.path.exists(TMP_FILE):
    print('Cleaning up old temp file.')
    os.remove(TMP_FILE)

SERVER_DATETIME, URL = get_latest_version(ARGS.experimental)

if SERVER_DATETIME > CURRENT_ARCHIVE_DATETIME or ARGS.force:
    print('New version of Factorio available.')

    if ARGS.check_only:
        exit(10)

    download_file(URL, TMP_FILE)
    print('Downloaded new version to {}.'.format(TMP_FILE))

    if not os.path.exists(TMP_STAGING):
        print('Creating staging folder {}.'.format(TMP_STAGING))
        os.mkdir(TMP_STAGING, 0o755)

    NEW_FACTORIO = extract_factorio(TMP_FILE, TMP_STAGING)

    print('Stopping Factorio.')
    return_code = subprocess.run(['systemctl', 'stop', 'factorio']).returncode
    if return_code != 0:
        raise RuntimeError
    print('Stopped Factorio.')

    print('Copying new files.')
    # TODO: Figure out where the current version is installed. This assumes /opt/.
    return_code = subprocess.run(['cp', '-R', NEW_FACTORIO, '/opt/']).returncode
    if return_code != 0:
        raise RuntimeError
    print('Copied new files.')

    print('Starting Factorio.')
    return_code = subprocess.run(['systemctl', 'start', 'factorio']).returncode
    if return_code != 0:
        raise RuntimeError
    print('Started Factorio.')

    print('Updating current archive.')
    shutil.move(TMP_FILE, CURRENT_ARCHIVE)
else:
    print('Factorio is already up to date.')

shutil.rmtree(TMP_STAGING)
