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
from adup.logging import error, info
from adup.utils import get_engine


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.option(
    "-f",
    "--force",
    "force",
    default=False,
    is_flag=True,
    help="Force the initialization.",
)
@click.pass_obj
def cli(ctx, force):
    """
    Initialize ADUP database.
    """
    # Get backend from config file
    backend = get_engine(ctx.config)

    # Initialize the database
    try:
        from adup.backends import initdb

        initdb(backend, force)

        info("Database initialized.")
        info("You can now update the database with files using 'updatedb' command.")
    except Exception as exc:  # pragma: no cover
        error("FATAL: cannot initialize database: %s" % exc, fg="red")
        sys.exit(1)
