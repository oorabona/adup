import errno
import glob
import os
import sys

import click
from alive_progress import alive_bar

from adup.backends import refreshdb, updatedb
from adup.cli import cli
from adup.utils import debug, getEngine


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.option(
    "-i",
    "--include",
    "include",
    default=[f"{os.path.curdir}"],
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
    Update ADUP database.
    """
    # Get backend from config file
    getEngine(ctx.config)

    # Get the list of all the paths to check
    pathsSection = ctx.config.items("paths")

    # Add the paths from the command line
    paths = []
    paths.extend(include)

    # Add the paths from the command line
    if "include" in pathsSection:
        for path in pathsSection.include:
            paths.extend(path)

    # Remove empty paths and duplicates
    paths = list({path.strip() for path in paths if path})
    debug(f"Included Paths: {paths}")

    # Remove the paths excluded from the command line
    for path in exclude:
        if path in paths:
            paths.remove(path)

    # Remove the paths excluded from the config file
    if "exclude" in pathsSection:
        for path in pathsSection.exclude:
            if path in paths:
                paths.remove(path)

    debug(f"After Excluded Paths: {paths}")
    if verbose:
        click.secho("Updating information from paths: %s" % ", ".join(paths), fg="green")

    with alive_bar(0, bar="blocks", spinner="dots_waves", dual_line=True, disable=not progress) as bar:
        for path in paths:
            for filename in glob.iglob(f"{path}**/**", recursive=True):
                if verbose:
                    click.secho("Updating information for : %s" % filename, fg="green")

                try:
                    stat = os.stat(filename)

                    # Check if the file is a regular file
                    if not stat.st_mode & 0o100000:
                        if verbose:
                            click.secho("File %s is not a regular file, skipping" % filename, fg="red")
                        continue

                    updatedb(os.path.dirname(filename), os.path.basename(filename), stat)
                    bar()
                except OSError as e:  # pragma: no cover
                    if e.errno == errno.ENOENT:
                        click.secho("File %s does not exist, skipping" % filename, fg="red")
                        continue
                    else:
                        raise
                except Exception as e:  # pragma: no cover
                    click.secho("Error while updating {}: {}".format(filename, e), fg="red")
                    continue

    if refresh:
        if verbose:
            click.secho("Refreshing database", fg="green")
        nbFilesBefore, nbFilesAfter = refreshdb()
        if verbose:
            click.secho(f"Removed {nbFilesBefore - nbFilesAfter} files from the database", fg="green")

    sys.exit(0)
