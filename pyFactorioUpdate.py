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
import glob
import os
import shutil
import tarfile
import subprocess
import logging
import requests
import yaml


def remove_mods(requested_mods):
    '''remove mods that are not in the defined yaml'''
    installed = glob.glob(ARGS.mods_dir + '*.zip')

    for zip_file in installed:
        if os.path.basename(zip_file) not in [
                mod['file_name'] for mod in requested_mods
        ]:
            os.remove(zip_file)


def get_mods():
    '''Get mods requested and installed'''
    manifest = requests.get(MODMANIFEST, allow_redirects=True)
    config = dict(yaml.safe_load(manifest.content))
    requested_mods = []
    updates_available = False
    for mod in config['mods']:
        update_needed = False
        mod_path = ''
        old_zips = glob.glob(ARGS.mods_dir + mod['name'] + '*.zip')
        if old_zips:
            mod_path = old_zips[0]
        if os.path.exists(mod_path):
            local_mod_time = datetime.utcfromtimestamp(
                os.path.getctime(mod_path))
        else:
            local_mod_time = datetime.fromtimestamp(0)
        metadata = requests.get(
            'https://mods.factorio.com/api/mods/{name}'.format(
                name=mod['name'])).json()
        released = datetime.strptime(metadata['releases'][-1]['released_at'],
                                     '%Y-%m-%dT%H:%M:%S.%fZ')
        if released > local_mod_time:
            update_needed = True
            updates_available = True
        mod_url = 'https://mods.factorio.com/' + metadata['releases'][-1][
            'download_url'] + '?username=' + APIUSER + '&token=' + APITOKEN
        requested_mods.append({
            'file_name':
            metadata['releases'][-1]['file_name'],
            'old_path':
            mod_path,
            'url':
            mod_url,
            'update_needed':
            update_needed
        })
    return requested_mods, updates_available


def update_mods(requested_mods):
    '''Downloads mods that need updating'''
    for mod in requested_mods:
        if mod['update_needed']:
            download_file(mod['url'],
                          os.path.join(ARGS.mods_dir, mod['file_name']))
            if mod['old_path']:
                os.remove(mod['old_path'])


def download_file(src, dest):
    '''Downloads a file.'''
    download = requests.get(src, stream=True)
    with open(dest, 'wb') as file_descriptor:
        for chunk in download.iter_content(chunk_size=128):
            file_descriptor.write(chunk)
    file_descriptor.close()
    LOGGER.debug("Downloaded %s to %s", src, dest)


def extract_factorio(archive, dest):
    '''Extracts the downloaded tar.'''
    archive = tarfile.open(archive)
    archive.extractall(dest)
    return os.path.join(dest, 'factorio')


def get_latest_version(url):
    '''Returns the datetime of the package available for download and the URL
       to retrieve that package.
    '''
    response = requests.head(url, allow_redirects=True)
    return datetime.strptime(response.headers['Last-Modified'],
                             '%a, %d %b %Y %H:%M:%S %Z')


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
     'Exits with 0 if no new package availble, 10 if newer version available.'
     ),
    action='store_true')
PARSER.add_argument('--mods',
                    help='Install/update mods from a manifest file',
                    action='store_true')
PARSER.add_argument(
    '--api_user',
    help='User mod api auth',
)
PARSER.add_argument('--api_token', help='Token for mod api auth')
PARSER.add_argument('--mod_manifest', help='Mod manifest location.')
PARSER.add_argument('--mods_dir',
                    default='/opt/factorio/mods/',
                    help='Directory to manage mods.')

# TODO: Allow selection of logging level at run time.
# PARSER.add_argument(
#     '--log_level',
#     choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
#     default='INFO')
ARGS = PARSER.parse_args()

LOGGER = logging.getLogger()
LOG_FILE = logging.FileHandler('/var/log/factorio_updater.log')
LOG_FILE.setLevel(logging.DEBUG)
LOG_CONSOLE = logging.StreamHandler()
LOG_CONSOLE.setLevel(logging.WARNING)

FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_FILE.setFormatter(FORMATTER)
LOG_CONSOLE.setFormatter(FORMATTER)

LOGGER.addHandler(LOG_FILE)
LOGGER.addHandler(LOG_CONSOLE)

CURRENT_ARCHIVE = '/opt/factorio-updater/current'
if os.path.exists(CURRENT_ARCHIVE):
    CURRENT_ARCHIVE_TS = os.path.getctime(CURRENT_ARCHIVE)
    CURRENT_ARCHIVE_DATETIME = datetime.utcfromtimestamp(CURRENT_ARCHIVE_TS)
else:
    LOGGER.warning(
        'Unable to determine timestamp of currently installed instance')
    CURRENT_ARCHIVE_DATETIME = datetime.fromtimestamp(0)

CHECKMODS = ARGS.mods
APIUSER = ARGS.api_user
APITOKEN = ARGS.api_token
MODMANIFEST = ARGS.mod_manifest
if CHECKMODS and (APIUSER == '' or APITOKEN == ''):
    LOGGER.warning('Mod check requested but no credentials supplied')
    CHECKMODS = False
if CHECKMODS and MODMANIFEST == '':
    LOGGER.warning('Mod check requested but no manifest specified')
    CHECKMODS = False

TMP_DIR = ARGS.tmp_dir
TMP_FILE = os.path.join(TMP_DIR, 'archive.tar')
TMP_STAGING = os.path.join(TMP_DIR, 'staging')

if not os.path.exists(TMP_DIR):
    LOGGER.debug('Creating temporary directory %s.', TMP_DIR)
    os.mkdir(TMP_DIR, 0o755)

if os.path.exists(TMP_FILE):
    LOGGER.info('Cleaning up old temp file.')
    os.remove(TMP_FILE)
URL = 'https://www.factorio.com/get-download/{revision}/headless/linux64'.format(
    revision='latest' if ARGS.experimental else 'stable')
SERVER_DATETIME = get_latest_version(URL)

SERVER_UPDATE = False

if SERVER_DATETIME > CURRENT_ARCHIVE_DATETIME:
    LOGGER.info('Server update available')
    SERVER_UPDATE = True

if CHECKMODS:
    LOGGER.info('Checking for mod updates')
    MODS, MOD_UPDATES = get_mods()

if SERVER_UPDATE or MOD_UPDATES or ARGS.force:

    if ARGS.check_only:
        exit(10)

    LOGGER.debug('Stopping Factorio.')
    return_code = subprocess.run(['systemctl', 'stop', 'factorio']).returncode
    if return_code != 0:
        raise RuntimeError

    LOGGER.debug('Stopped Factorio.')

    if SERVER_UPDATE:
        download_file(URL, TMP_FILE)
        LOGGER.debug('Downloaded new version to %s.', TMP_FILE)

        if not os.path.exists(TMP_STAGING):
            LOGGER.debug('Creating staging folder %s.', TMP_STAGING)
            os.mkdir(TMP_STAGING, 0o755)

        NEW_FACTORIO = extract_factorio(TMP_FILE, TMP_STAGING)

        LOGGER.debug('Copying new files.')
        # TODO(GitGerby): Figure out where the current version is installed. This assumes /opt/.
        return_code = subprocess.run(['cp', '-R', NEW_FACTORIO,
                                      '/opt/']).returncode
        if return_code != 0:
            raise RuntimeError
        LOGGER.debug('Copied new files.')
        LOGGER.debug('Updating current archive.')
        shutil.move(TMP_FILE, CURRENT_ARCHIVE)

        LOGGER.info('Factorio has been updated.')

    update_mods(MODS)
    remove_mods(MODS)

    LOGGER.debug('Starting Factorio.')
    return_code = subprocess.run(['systemctl', 'start', 'factorio']).returncode
    if return_code != 0:
        raise RuntimeError
    LOGGER.debug('Started Factorio.')

else:
    LOGGER.info('Factorio is already up to date.')

if os.path.exists(TMP_STAGING):
    LOGGER.info('Cleaning staging directory')
    shutil.rmtree(TMP_STAGING)
