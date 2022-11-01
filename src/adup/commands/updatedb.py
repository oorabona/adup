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

import errno
import os
import sys

import click
from alive_progress import alive_bar

from adup.backends import refreshdb, updatedb
from adup.cli import cli
from adup.logging import debug, error, info, warn
from adup.utils import get_engine, get_multi_value_option


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.option(
    "-i",
    "--include",
    "include",
    default=[],
    show_default=True,
    help="Add this path to the list.",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    multiple=True,
)
@click.option(
    "-e",
    "--exclude",
    "exclude",
    default=[],
    show_default=True,
    help="Remove this path from the list.",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    multiple=True,
)
@click.option(
    "-v",
    "--verbose",
    "verbose",
    is_flag=True,
    default=False,
    show_default=True,
    help="Verbose mode.",
)
@click.option(
    "-r",
    "--refresh",
    "refresh",
    is_flag=True,
    default=False,
    show_default=True,
    help="Refresh the database (i.e. remove deleted files in the database).",
)
@click.option(
    "--progress",
    "progress",
    default=False,
    help="Show progress bar.",
    is_flag=True,
)
@click.pass_obj
def cli(ctx, include, exclude, verbose, refresh, progress):
    """
    Update ADUP database with files metadata.
    """
    # Get backend from config file
    get_engine(ctx.config)

    # Get the list of all the paths to check
    pathsSection = ctx.config["paths"]

    # Get the list of paths to include from the config file
    # and merge with the list of paths to include from the command line
    include_path = list(include) + get_multi_value_option(pathsSection, "include[]")

    # Remove empty paths and duplicates
    include_paths = list({os.path.abspath(path.strip()) for path in include_path if path})
    debug(f"Included Paths: {include_paths}")

    # Get the list of paths to exclude from the config file
    # and merge with the list of paths to exclude from the command line
    exclude_path = list(exclude) + get_multi_value_option(pathsSection, "exclude[]")

    # Remove empty paths and duplicates
    exclude_paths = list({os.path.abspath(path.strip()) for path in exclude_path if path})
    debug(f"Excluded Paths: {exclude_paths}")

    # Remove excluded paths from included paths
    paths = [path for path in include_paths if path not in exclude_paths]

    debug(f"After Excluded Paths: {paths}")
    if verbose:
        info("Updating information from paths: %s" % ", ".join(paths))

    with alive_bar(manual=True, bar="blocks", spinner="dots_waves", dual_line=True, disable=not progress) as bar:
        current = 0
        for path in paths:
            current += 1
            for entry in os.scandir(path):
                if entry.is_dir(follow_symlinks=False):
                    if entry.name.startswith(".") or entry.path in exclude_paths:
                        continue
                    paths.append(entry.path)
                    continue
                if entry.is_file(follow_symlinks=False):
                    filename = entry.path

                    if verbose:
                        info("Updating information for : %s" % filename)

                    try:
                        stat = entry.stat(follow_symlinks=False)
                        bar.text(f"Updating information for : {filename}")

                        # Check if the file is a regular file
                        if not stat.st_mode & 0o100000:
                            if verbose:
                                warn("File %s is not a regular file, skipping" % filename)
                            continue

                        updatedb(os.path.dirname(filename), os.path.basename(filename), stat)

                        # Update progress bar only if progress is made
                        progress = current / len(paths)
                        if bar.current() < progress:
                            bar(progress)
                    except OSError as e:  # pragma: no cover
                        if e.errno == errno.ENOENT:
                            error("File %s does not exist, skipping" % filename)
                            continue
                        else:
                            raise
                    except Exception as e:  # pragma: no cover
                        error("Error while updating {}: {}".format(filename, e))
                        continue

    if refresh:
        if verbose:
            info("Refreshing database")
        nbFilesBefore, nbFilesAfter = refreshdb()
        if verbose:
            info(f"Removed {nbFilesBefore - nbFilesAfter} files from the database")

    sys.exit(0)
