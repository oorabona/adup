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

import errno
import os
import sys

import click

from adup.cli import cli
from adup.utils import TPL_CONFIG_FILE, debug


@click.group()
def cli():  # noqa: F811
    pass


@cli.command()
@click.option(
    "-e",
    "--editor",
    "editor",
    default="vim",
    show_default=True,
    help="Editor to use.",
    type=click.Path(dir_okay=False),
)
@click.option(
    "-f",
    "--force",
    "force",
    default=False,
    is_flag=True,
    help="Force the initialization.",
)
@click.pass_obj
def cli(ctx, editor, force):
    """
    Initialize ADUP configuration file.
    """

    filename = click.format_filename(ctx.configfile)
    debug("Configuration file: %s" % filename)

    try:
        # Create the directory if it does not exist
        # and if it exists, do not raise any exception !
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        if force:
            mode = "w"
        else:
            mode = "x"

        # Create config file with the default contents
        with open(filename, mode) as f:
            f.write(TPL_CONFIG_FILE)
            f.flush()

        # In this configuration, with a filename, this always returns None
        # so no need to check the return value
        click.edit(
            require_save=True,
            filename=filename,
            editor=editor,
        )

        click.secho("Configuration file '%s' created successfully." % filename, fg="green")
        click.secho(
            "You can now edit it again if needed, and run 'adup initdb' to initialize the database.", fg="green"
        )
        sys.exit(0)
    except click.UsageError:  # pragma: no cover
        click.secho("FATAL: cannot edit configuration file '%s' !" % filename, fg="red")
        sys.exit(1)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            if not force:
                click.secho(
                    "FATAL: configuration file '%s' already exists !" % filename,
                    fg="red",
                )
                sys.exit(1)
        else:  # pragma: no cover
            click.secho(
                "FATAL: cannot create directories for configuration file '%s' !" % filename,
                fg="red",
            )
            sys.exit(1)
