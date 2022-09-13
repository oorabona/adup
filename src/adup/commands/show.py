import sys

import click
from tabulate import tabulate

from adup.cli import cli
from adup.utils import getEngine, getMatchingConditions, makeArrayFromDict


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
    getEngine(ctx.config)

    # Process conditions
    listOfConditions = getMatchingConditions("every")

    # Let the backend do the job
    try:
        from adup.backends import showDuplicates

        columns, results = showDuplicates(listOfConditions, name, path)
    except Exception as exc:  # pragma: no cover
        click.secho("FATAL: cannot execute command in database: %s" % exc, fg="red")
        sys.exit(1)

    # tabulate results
    if len(results) > 0:
        click.secho(f"Total number of occurrences: {len(results)}", bold=True)

        if details is True:
            click.secho(tabulate(results, headers=[name for name in columns], tablefmt="psql"))

        # Show summary
        click.secho(f"Summary for {name} ({path}):", bold=True)

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
        arrayOfOccurrencePerCondition = makeArrayFromDict(
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
        click.secho("No duplicates found.", fg="yellow")

    sys.exit(0)
