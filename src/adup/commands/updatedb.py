import errno
import os
import sys

import click
from alive_progress import alive_bar

from adup.backends import refreshdb, updatedb
from adup.cli import cli
from adup.utils import debug, get_multi_value_option, getEngine


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
    Update ADUP database.
    """
    # Get backend from config file
    getEngine(ctx.config)

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
        click.secho("Updating information from paths: %s" % ", ".join(paths), fg="green")

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
                        click.secho("Updating information for : %s" % filename, fg="green")

                    try:
                        stat = entry.stat(follow_symlinks=False)
                        bar.text(f"Updating information for : {filename}")

                        # Check if the file is a regular file
                        if not stat.st_mode & 0o100000:
                            if verbose:
                                click.secho("File %s is not a regular file, skipping" % filename, fg="red")
                            continue

                        updatedb(os.path.dirname(filename), os.path.basename(filename), stat)

                        # Update progress bar only if progress is made
                        progress = current / len(paths)
                        if bar.current() < progress:
                            bar(progress)
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
