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

import sys

import click

from adup.cli import cli
from adup.logging import debug, error
from adup.utils import get_engine, get_matching_conditions


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
        click.echo(
            " ".join(
                [
                    click.style(f"{which.title()}", fg=whichFg, bold=True),
                    click.style(f"file(s) of {', '.join(conditions)} will be", bold=True),
                    click.style(f"{operation}ed", fg=operationFg, bold=True),
                ]
            )
        )

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
        error("FATAL: cannot execute command in database: %s" % exc)
        sys.exit(1)

    sys.exit(0)
