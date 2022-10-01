import sys

import click

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
    type=click.Choice(["select", "unselect"]),
)
@click.argument(
    "which",
    nargs=1,
    type=click.Choice(["older", "newer", "larger", "smaller", "all", "empty"]),
)
@click.option(
    "-n",
    "--name",
    "name",
    default=None,
    help="File name to apply to (only one occurrence, may be a glob pattern).",
    type=click.STRING,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=None,
    help="Path to apply to (only one occurrence, may be a glob pattern).",
    type=click.STRING,
)
@click.pass_obj
def cli(ctx, conditions, operation, which, name, path):
    """
    Marks duplicates as such in the database.
    """
    # Get backend from config file
    get_engine(ctx.config)

    # Process conditions
    debug("Conditions given in command line: {}".format(conditions))
    listOfConditions = get_matching_conditions([conditions])
    debug("List of conditions to apply:")
    for condition in listOfConditions:
        debug(" - {}".format(" and ".join(condition)))

    if which == "all":
        whichFg = "red"
    else:
        whichFg = "yellow"

    if operation == "unselect":
        operationFg = "green"
    elif operation == "select":
        operationFg = "red"
    else:  # should never happen
        raise ValueError("Invalid value for 'operation'")  # pragma: no cover

    for conditions in listOfConditions:
        click.secho(f"{which.title()} ", bold=True, fg=whichFg, nl=False)
        click.secho(f"file(s) of {', '.join(conditions)} will be marked to ", bold=True, nl=False)
        click.secho(f"{operation}", bold=True, fg=operationFg)

    # Let the backend do the job
    try:
        from adup.backends import mark_duplicates

        results = mark_duplicates(listOfConditions, operation, which, name, path)
        selectStyle = click.style("select", fg="red", bold=True)
        unselectStyle = click.style("unselect", fg="green", bold=True)
        grandTotalSelectCount = 0
        grandTotalUnselectCount = 0
        grandTotalSelectSize = 0
        grandTotalUnselectSize = 0
        for key, value in results.items():
            if len(value) > 0:
                totalCount = sum(x[1] for x in value)
                totalSize = sum(x[2] for x in value)
                for i in range(len(value)):
                    keep, count, size = value[i]
                    if keep is True:
                        grandTotalSelectCount += count
                        grandTotalSelectSize += size
                        click.secho(
                            f"[{round(count/totalCount*100,2)}%] {count} of {totalCount} files to {selectStyle} representing {size} of {totalSize} bytes on {key}",
                            bold=True,
                        )
                    elif value[i][0] is False:
                        grandTotalUnselectCount += count
                        grandTotalUnselectSize += size
                        click.secho(
                            f"[{round(count/totalCount*100,2)}%] {count} of {totalCount} files to {unselectStyle} representing {size} of {totalSize} bytes on {key}",
                            bold=True,
                        )

        click.secho(
            f"Grand total: {grandTotalSelectCount} files to {selectStyle} representing {grandTotalSelectSize} bytes",
            bold=True,
        )
        click.secho(
            f"Grand total: {grandTotalUnselectCount} files to {unselectStyle} representing {grandTotalUnselectSize} bytes",
            bold=True,
        )
    except Exception as exc:  # pragma: no cover
        click.secho("FATAL: cannot execute command in database: %s" % exc, fg="red")
        sys.exit(1)

    sys.exit(0)
