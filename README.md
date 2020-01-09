# pyFactorioUpdater
[![Build Status](https://travis-ci.org/GitGerby/pyFactorioUpdate.svg?branch=master)](https://travis-ci.org/GitGerby/pyFactorioUpdate)

## About
pyFactorioUpdate was created to eliminate the toil involved in updating a
headless Factorio server. When run the script will compare the last-modified
header of the Factorio archive available for download against the creation time
of the most recently downloaded archive, if the web version is newer it will be
fetched and installed. When run as a cron job the script can completely automate the updating of a headless Factorio instance.

## Requirements
* Python 3
* factorio-rcon-py library
* Factorio Headless
* Systemd configured to control Factorio server instance
* Factorio must live in /opt/factorio at this time.

## Installation
Download pyFactorioUpdater to `/opt/factorio_updater/`, run with cron on your preferred schedule.

## Arguments
* `--check_only` will only compare the latest availalble version to the version on disk without out downloading or updating. If a newer version is available pyFactorioUpdater with exit with 10 rather than 0.
* `-e` or `--experimental` will use Factorio's experimental track rather than stable, defaults to no.
* `-f` or `--force` will ignore the last modified time on the server and force a download and install of the latest selected track; defaults to no.
* `--tmp_directory` specifies where download and staging of the new Factorio archive should occur.  Defaults to `/tmp/factorio_updater/`
* `--rcon_port` specifies port for RCON client communication. Default is `27015`.
* `--rcon_passowrd` defines password for RCON client communication. In-game broadcasting will not work without this argument set.