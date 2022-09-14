#!/usr/bin/env python
# -*- coding: utf8 -*-
__metaclass__ = type

import importlib
import os
import pkgutil
import sys
import typing

import click

import adup.utils as utils

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


class Adup(object):
    def __init__(self, command=None, configfile=None, debug=False):
        self.configfile = configfile
        self.debug = debug
        if command != "init":
            try:
                self.config = utils.loadConfig(configfile)
            except Exception as exc:
                click.secho("FATAL: cannot load configuration file: %s" % exc, fg="red")
                sys.exit(1)


@click.version_option()
@click.command(
    cls=MyCLI,
    context_settings=CONTEXT_SETTINGS,
)
@click.option(
    "-c",
    "--config",
    "configfile",
    default=utils.get_config_filepath,
    show_default=True,
    help="Config file to use.",
    type=click.Path(dir_okay=False),
)
@click.option("--debug/--no-debug", default=False, envvar="DEBUG", help="Enable debug mode.")
@click.pass_context
def cli(ctx, configfile, debug):
    """
    ADUP is a tool to manage your files and operate (bulk) operations on them.
    """
    ctx.obj = Adup(ctx.invoked_subcommand, configfile, debug)
    utils.setup_logging(debug)
    utils.debug(f"Debug mode is {'on' if debug else 'off'}")


if __name__ == "__main__":
    cli()
