import sys

import click
from tabulate import tabulate

from adup.cli import cli
from adup.utils import debug, get_engine, get_matching_conditions


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.option(
    "-t",
    "--type",
    "conditions",
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
    get_engine(ctx.config)

    # Process conditions
    debug("Conditions given in command line: {}".format(conditions))
    listOfConditions = get_matching_conditions([conditions])
    debug("List of conditions to apply:")
    for condition in listOfConditions:
        debug(" - {}".format(" and ".join(condition)))

    # Debug
    debug("List of columns to hide:")
    for column in hideColumns:
        debug(" - {}".format(column))

    click.secho(f"Listing files marked as {operation} for condition '{conditions}'.", bold=True)

    # Let the backend do the job
    try:
        from adup.backends import list_duplicates

        columns, results = list_duplicates(operation, listOfConditions, hideColumns)
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
        click.secho(f"No {operation} duplicates found for this combination '{conditions}' !", fg="yellow")

    sys.exit(0)
