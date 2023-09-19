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


import importlib.metadata
import os
import pkgutil
import sys
import typing

import click

import adup.utils as utils
from adup.logging import debug, error, setup_logging

__version__ = importlib.metadata.version("adup")

CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    auto_envvar_prefix="ADUP",
    token_normalize_func=lambda x: x.lower(),
)

plugin_folder = os.path.join(os.path.dirname(__file__), "commands")


class MyCLI(click.MultiCommand):
    def list_commands(self, ctx: click.Context) -> typing.List[str]:
        rv = []
        for _importer, modname, _ispkg in pkgutil.iter_modules([plugin_folder]):
            rv.append(modname)
        rv.sort()
        return rv

    def get_command(self, ctx: click.Context, name: str) -> typing.Callable:
        try:
            mod = importlib.import_module("adup.commands." + name)
        except ImportError:  # pragma: no cover
            return
        return mod.cli


class Adup:
    def __init__(self, command=None, configfile=None, debug=False):
        self.configfile = configfile
        self.debug = debug
        setup_logging(debug)

        if command != "init":
            try:
                self.config = utils.load_config(configfile)
            except Exception as exc:
                error(f"FATAL: cannot load configuration file: {exc}")
                error("Please run 'adup init' first.")
                sys.exit(1)


@click.version_option(__version__)
@click.command(
    cls=MyCLI,
    context_settings=CONTEXT_SETTINGS,
)
@click.option(
    "-c",
    "--config",
    "configfile",
    default=utils.get_config_filepath,
    help="Config file to use.",
    type=click.Path(dir_okay=False),
)
@click.option(
    "--debug/--no-debug", "is_debug", default=False, show_default=True, envvar="DEBUG", help="Enable debug mode."
)
@click.pass_context
def cli(ctx, configfile, is_debug):
    """
    ADUP is a tool to manage your files and operate (bulk) operations on them.
    """
    ctx.obj = Adup(ctx.invoked_subcommand, configfile, is_debug)
    debug(f"Debug mode is {'on' if is_debug else 'off'}")


if __name__ == "__main__":
    cli(prog_name="adup")
