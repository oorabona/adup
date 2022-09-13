import sys

import click
from tabulate import tabulate

from adup.cli import cli
from adup.utils import debug, getEngine, getMatchingConditions


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
@click.argument(
    "operation",
    nargs=1,
    type=click.Choice(["selected", "unselected"]),
)
@click.option(
    "--hide",
    "hideColumns",
    default=[],
    help="Hide columns.",
    type=click.Choice(["name", "path", "size", "mtime", "hash", "hash4k"]),
    multiple=True,
)
@click.pass_obj
def cli(ctx, conditions, operation, hideColumns):
    """
    List files marked as duplicates.
    """
    # Get backend from config file
    getEngine(ctx.config)

    # Process conditions
    listOfConditions = getMatchingConditions(conditions)

    # Debug
    debug("Conditions: %s" % listOfConditions)
    debug("hideColumns: '%s'" % " and ".join(hideColumns))

    click.secho(f"Listing files marked as {operation} for condition '{conditions}'.", bold=True)

    # Let the backend do the job
    try:
        from adup.backends import listDuplicates

        columns, results = listDuplicates(operation, listOfConditions, hideColumns)
    except Exception as exc:  # pragma: no cover
        click.secho("FATAL: cannot execute command in database: %s" % exc, fg="red")
        sys.exit(1)

    # tabulate results
    if len(results) > 0:
        click.secho(tabulate(results, headers=[name for name in columns], tablefmt="psql"))
        index = [index for index, name in enumerate(columns) if name == "size"][0]
        totalSize = sum(x[index] for x in results)
        click.secho(f"Total: {len(results)} files / {totalSize} bytes", bold=True)
    else:
        click.secho(f"No duplicates found for this combination '{conditions}' !", fg="yellow")

    sys.exit(0)
