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
from adup.utils import do_file_operation


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
    "--to",
    "to",
    default=None,
    help="Path to copy files to.",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True, allow_dash=False),
    prompt="Path to copy files to",
    required=True,
)
@click.option(
    "-n",
    "--dry-run",
    "dryrun",
    default=False,
    help="Do not actually copy files, just show what would be done.",
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
def cli(ctx, conditions, operation, to, dryrun, verbose, progress):
    """
    Copy all selected files in the database to an user-defined path.
    """

    # operate generically
    # since alive-progress works by "disabling" option, we need to reverse
    progressBar = not progress
    do_file_operation(conditions, operation, ctx.config, to, dryrun, verbose, "copy", progressBar)

    sys.exit(0)
