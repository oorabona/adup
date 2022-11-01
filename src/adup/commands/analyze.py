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
from adup.exceptions import NoFileInDatabase
from adup.logging import debug, error, info
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
    show_default=True,
)
@click.pass_obj
def cli(ctx, conditions):
    """
    Performs analyses to find duplicate files in the database.
    """
    # Get backend from config file
    get_engine(ctx.config)

    # Process conditions
    debug("Conditions given in command line: {}".format(conditions))
    listOfConditions = get_matching_conditions([conditions])
    debug("List of conditions to apply:")
    for condition in listOfConditions:
        debug(" - {}".format(" and ".join(condition)))

    # Get the list of all hashes with more than one occurrence
    results = {}
    try:
        from adup.backends import analyze_duplicates

        for conditions in listOfConditions:
            count, size = analyze_duplicates(conditions)
            results[" and ".join(conditions)] = count, size
    except NoFileInDatabase:
        error("No file in database. Nothing to do. Please run 'updatedb' command first.")
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        error("FATAL: cannot execute command in database: %s" % exc)
        sys.exit(1)

    for key, value in results.items():
        if value[0] > 0:
            info("Found %d possible duplicates (total size: %d bytes) for %s" % (value[0], value[1], key))

    sys.exit(0)
