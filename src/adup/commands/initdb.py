import sys

import click

from adup.cli import cli
from adup.utils import getEngine


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
    backend = getEngine(ctx.config)

    # Initialize the database
    try:
        from adup.backends import initdb

        initdb(backend, force)
    except Exception as exc:  # pragma: no cover
        click.secho("FATAL: cannot initialize database: %s" % exc, fg="red")
        sys.exit(1)
