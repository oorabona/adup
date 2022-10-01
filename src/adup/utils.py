# Copyright Olivier ORABONA <olivier.orabona@gmail.com> and contributors.
# All Rights Reserved.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import configparser
import itertools
import os
import shutil
import sys
from time import sleep

import click
from alive_progress import alive_bar

from adup.logging import debug, error, info, warn


# Convert string representation of true / false to boolean
def str2bool(v):
    if v.lower() in ("yes", "y", "true", "t", "on", "1"):
        return True
    elif v.lower() in ("no", "n", "false", "f", "off", "0"):
        return False
    else:
        raise TypeError("Boolean value expected.")


def make_array_from_dict(*args):
    a = []
    for i in args:
        for k, v in i.items():
            indices = [index for index, item in enumerate(a) if item[0] == k]
            if len(indices) > 0:
                for index in indices:
                    a[index].append(v)
            else:
                a.append([k, v])

    return a


def get_config_filepath():
    return (
        os.path.expanduser("~/.config/adup/adup.conf")
        if os.environ.get("USER")
        else os.path.join("/etc", "adup", "adup.conf")
    )


def get_db_filepath():
    return (
        os.path.expanduser("~/.config/adup/adup.db")
        if os.environ.get("USER")
        else os.path.join("/etc", "adup", "adup.db")
    )


DEFAULT_CONFIG = """
[env]
"""

# Populate this section with environment variables
for key in os.environ.keys():
    DEFAULT_CONFIG += key + " = " + os.environ[key] + "\n"

DEFAULT_CONFIG += f"""
[global]
backend = sqlite

[paths]
include[] =
exclude[] =

[sqlalchemy]
echo = False
future = True

[sqlite]
db = {get_db_filepath()}
"""

# Below is the default template for the configuration file.
TPL_CONFIG_FILE = f"""
# Comments should start with a # and must be full lines
[global]

# At least one backend must be choosen, for now only sqlite is supported.
# This must be something SQLAlchemy understands.
backend = sqlite

# If you want to specify common paths to include and exclude, you can do it here.
# You can also specify them on the command line.
# Note : excluding paths is done after including paths.
[paths]
include[] =
exclude[] =

# Specific parameters for Alchemy should be set here.
[sqlalchemy]
echo = False

# The following options are used by the sqlite3 backend.
[sqlite]

# The database file to use.
db = {get_db_filepath()}
"""

# Helper functions to handle multi value options
config_multi_value_dict = {}


def multi_value_option(option):
    _option = option.lower()
    if _option.endswith("[]"):
        _option = _option[:-2]

        # Given a key get the following auto increment value
        # e.g. if key is foo, then foo1, foo2, foo3, etc.
        if config_multi_value_dict.get(_option) is None:
            config_multi_value_dict[_option] = 1
        else:
            config_multi_value_dict[_option] += 1

        return f"{_option}_{config_multi_value_dict[_option]}"

    return _option


def get_multi_value_option(cp, option):
    _option = option.lower()
    if _option.endswith("[]"):
        _option = _option[:-2]
        max_option_index = config_multi_value_dict.get(_option)
        if max_option_index is None:
            return None
        else:
            return [cp[f"{_option}_{i}"] for i in range(1, max_option_index + 1)]

    return _option


def load_config(configfile):
    debug("Loading config file %s" % configfile)

    with open(configfile) as f:
        config = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation(),
            allow_no_value=True,
        )
        config.optionxform = multi_value_option
        config.read_string(DEFAULT_CONFIG)
        config.read_file(f)
        return config


# Returns an Engine instance based on the configuration file
def get_engine(config):
    backend = config.get("global", "backend")
    try:
        from .backends import create_engine

        return create_engine(backend, config)
    except NotImplementedError:
        raise click.ClickException("Backend '%s' is not supported" % backend)
    except ImportError:
        raise click.ClickException("Could not import backends (backend %s)" % backend)


def get_matching_conditions(conditions=None):
    # Throw error if no conditions are specified
    if conditions is None or len(conditions) == 0:
        raise ValueError("No condition specified !")

    # All conditions
    allConditions = ["samehash4k", "samehash", "samemtime", "samesize", "samename"]

    # List conditions to apply from command line
    # by default, we apply only samehash condition
    # if condition is "all", we apply all conditions
    # if condition is "every", we apply all combinations of conditions
    if conditions.count("all") > 0:
        listOfConditions = [allConditions]
    elif conditions.count("every") > 0:
        listOfConditions = [list(x) for x in itertools.combinations(allConditions, 1)]
        for i in range(2, len(allConditions) + 1):
            listOfConditions.extend([list(x) for x in itertools.combinations(allConditions, i)])
    else:
        # Because `sort` returns None, we need to split in three lines :)
        listOfConditions = list(conditions)
        listOfConditions.sort()
        listOfConditions = [listOfConditions]

    return listOfConditions


def do_file_operation(conditions, operation, config, to, dryrun, verbose, fileOp, disable_progress_bar):
    """
    The place where the file operation is done
    """
    # Get backend from config file
    get_engine(config)

    # Process conditions
    listOfConditions = get_matching_conditions([conditions])
    debug("Conditions to apply : %s" % listOfConditions)

    # Let the backend do the job
    try:
        from .backends import list_duplicates

        columns, results = list_duplicates(operation, listOfConditions, [])
    except Exception as exc:
        error("FATAL: cannot execute command in database: %s" % exc)
        sys.exit(1)

    # tabulate results
    if len(results) > 0:
        index = [index for index, name in enumerate(columns) if name == "size"][0]
        totalSize = sum(x[index] for x in results)
        if verbose:
            info(
                f"Attempting to {fileOp} files according to condition '{' and '.join(conditions)}': {len(results)} files / {totalSize} bytes",
                bold=True,
            )

        # Compute available disk space in destination if not removing
        if fileOp != "remove":
            try:
                availableSpace = shutil.disk_usage(to).free
            except Exception as exc:
                error(f"ERROR: cannot compute available space in {to}: {exc}")
                sys.exit(1)

            if availableSpace < totalSize:
                error(
                    f"ERROR: not enough space in {to}: {availableSpace} bytes available, {totalSize} bytes needed, you need {totalSize-availableSpace} bytes required."
                )
                sys.exit(1)

        # Decide what to do based on fileOp
        if fileOp == "move":
            fnOp = shutil.move
        elif fileOp == "copy":
            fnOp = shutil.copy
        elif fileOp == "remove":
            fnOp = os.remove
        else:
            error(f"ERROR: unknown file operation {fileOp}")
            sys.exit(1)

        # Move files
        with alive_bar(
            len(results), bar="blocks", spinner="dots_waves", dual_line=True, disable=disable_progress_bar
        ) as bar:
            for result in results:
                sleep(1)
                filepath = f"{result[1]}{os.sep}{result[0]}"
                if dryrun is True:
                    if verbose is True:
                        if disable_progress_bar is False:
                            bar.text = f"{filepath} -> {to}"
                        else:
                            click.secho(f"DRY-RUN: would {fileOp} {filepath} to {to}... ", fg="yellow", nl=False)
                else:
                    try:
                        if fileOp == "remove":
                            fnOp(filepath)
                        else:
                            fnOp(filepath, to)
                    except Exception as exc:
                        error(f"ERROR: cannot {fileOp} {filepath} to {to}: {exc}", fg="red")
                        sys.exit(1)
                if verbose is True:
                    if disable_progress_bar is False:
                        bar.text = f"{filepath} -> {to} [OK]"
                    else:
                        click.secho("OK", fg="green")

                bar()
    else:
        warn(f"No file found in {operation} condition '{conditions}'.")

    return
