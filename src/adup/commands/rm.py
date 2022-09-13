import sys

import click

from adup.cli import cli
from adup.utils import do_file_operation


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.argument(
    "conditions",
    nargs=1,
    type=click.Choice(["samehash4k", "samehash", "samemtime", "samesize", "samename", "all", "every"]),
)
@click.argument(
    "operation",
    nargs=1,
    type=click.Choice(["selected", "unselected"]),
)
@click.option(
    "-n",
    "--dry-run",
    "dryrun",
    default=False,
    help="Do not actually remove files, just show what would be done.",
    is_flag=True,
)
@click.option(
    "-v",
    "--verbose",
    "verbose",
    default=False,
    help="Show more information.",
    is_flag=True,
)
@click.option(
    "--progress",
    "progress",
    default=False,
    help="Show progress bar.",
    is_flag=True,
)
@click.pass_obj
def cli(ctx, conditions, operation, dryrun, verbose, progress):
    """
    Remove all selected files in the database to an user-defined path.
    """

    # operate generically
    # since alive-progress works by "disabling" option, we need to reverse
    progressBar = not progress
    do_file_operation(conditions, operation, ctx.config, None, dryrun, verbose, "remove", progressBar)

    sys.exit(0)
