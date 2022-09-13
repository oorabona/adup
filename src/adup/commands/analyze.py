import sys

import click

from adup.cli import cli
from adup.utils import getEngine, getMatchingConditions


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.argument(
    "conditions",
    nargs=1,
    type=click.Choice(["samehash4k", "samehash", "samemtime", "samesize", "samename", "all", "every"]),
    default="samehash",
)
@click.pass_obj
def cli(ctx, conditions):
    """
    Performs analyses to find duplicate files in the database.
    """
    # Get backend from config file
    getEngine(ctx.config)

    # Process conditions
    listOfConditions = getMatchingConditions(conditions)

    # Get the list of all hashes with more than one occurrence
    results = {}
    try:
        from adup.backends import analyzeDuplicates

        for conditions in listOfConditions:
            count, size = analyzeDuplicates(conditions)
            results[" and ".join(conditions)] = count, size
    except Exception as exc:  # pragma: no cover
        click.secho("FATAL: cannot execute command in database: %s" % exc, fg="red")
        sys.exit(1)

    for key, value in results.items():
        if value[0] > 0:
            click.secho("Found %d possible duplicates (total size: %d) for %s" % (value[0], value[1], key), bold=True)

    sys.exit(0)
