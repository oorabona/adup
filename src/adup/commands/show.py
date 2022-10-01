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
from tabulate import tabulate

from adup.cli import cli
from adup.logging import error, info, warn
from adup.utils import get_engine, get_matching_conditions, make_array_from_dict


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.option(
    "-n",
    "--name",
    "name",
    default=None,
    help="File name to apply to (strict comparison, no glob).",
    type=click.STRING,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=None,
    help="Path to apply to (strict comparison, no glob).",
    type=click.STRING,
)
@click.option(
    "--details",
    "details",
    default=False,
    help="Show details.",
    is_flag=True,
)
@click.pass_obj
def cli(ctx, name, path, details):
    """
    Shows detailed information about a specific file/path.
    """
    # Get backend from config file
    get_engine(ctx.config)

    # Process conditions
    listOfConditions = get_matching_conditions("every")

    # Let the backend do the job
    try:
        from adup.backends import show_duplicates

        columns, results = show_duplicates(listOfConditions, name, path)
    except Exception as exc:  # pragma: no cover
        error("FATAL: cannot execute command in database: %s" % exc)
        sys.exit(1)

    # tabulate results
    if len(results) > 0:
        info(f"Total number of occurrences: {len(results)}")

        if details is True:
            click.secho(tabulate(results, headers=[name for name in columns], tablefmt="psql"))

        # Show summary
        info(f"Summary for {name} ({path}):")

        occurrencePerCondition = {}
        numberOfTimesSelected = {}
        numberOfTimesUnselected = {}
        listPathsForFile = []
        for result in results:
            # Compute the number of occurrence per condition
            occurrencePerCondition[result[0]] = occurrencePerCondition.get(result[0], 0) + 1
            numberOfTimesSelected[result[0]] = (
                numberOfTimesSelected.get(result[0], 0) + 1
                if result[7] is True
                else numberOfTimesSelected.get(result[0], 0)
            )
            numberOfTimesUnselected[result[0]] = (
                numberOfTimesUnselected.get(result[0], 0) + 1
                if result[7] is False
                else numberOfTimesUnselected.get(result[0], 0)
            )

            # Compute information about the file itself
            listPathsForFile.append([result[2], result[3], result[6], result[7]]) if [
                result[2],
                result[3],
                result[6],
                result[7],
            ] not in listPathsForFile else listPathsForFile

        # Make tabular output
        arrayOfOccurrencePerCondition = make_array_from_dict(
            occurrencePerCondition, numberOfTimesSelected, numberOfTimesUnselected
        )
        click.secho(
            tabulate(
                arrayOfOccurrencePerCondition,
                headers=["Condition", "Occurrences", "Number Of Times Selected", "Number Of Times Unselected"],
                tablefmt="psql",
            )
        )

        # Show paths
        click.secho(
            tabulate(listPathsForFile, headers=["Paths", "Size", "Modification Time", "Selected"], tablefmt="psql")
        )
    else:
        warn("No duplicates found.")

    sys.exit(0)
