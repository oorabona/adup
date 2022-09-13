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
        else:
            click.secho(
                "FATAL: cannot create directories for configuration file '%s' !" % filename,
                fg="red",
            )
            sys.exit(1)
