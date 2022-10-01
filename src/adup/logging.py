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

import inspect
import logging

import click


class ColorFormatter(logging.Formatter):
    colors = {
        "error": dict(fg="red"),
        "critical": dict(fg="red"),
        "debug": dict(fg="blue"),
        "warning": dict(fg="yellow"),
        "info": dict(fg="green", bold=True),
    }

    def format(self, record):
        if not record.exc_info:
            level = record.levelname.lower()
            msg = record.getMessage()
            if level in self.colors:
                prefix = click.style(f"{level}: ", **self.colors[level])
                msg = "\n".join(prefix + x for x in msg.splitlines())
            return msg
        return logging.Formatter.format(self, record)


class ClickHandler(logging.Handler):
    _use_stderr = True

    def emit(self, record):
        try:
            msg = self.format(record)
            click.echo(msg, err=self._use_stderr)
        except Exception:
            self.handleError(record)


_default_handler = ClickHandler()
_default_handler.formatter = ColorFormatter()


def setup_logging(is_debug):
    if is_debug:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(message)s",
            level=logging.INFO,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Customize logger
    logger = logging.getLogger()
    logger.handlers = [_default_handler]
    logger.propagate = False


# Kudos to https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
def debug(*args):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    # Get the filename
    filename = mod.__name__
    log = logging.getLogger(filename)
    return log.debug(*args)


def info(*args):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    # Get the filename
    filename = mod.__name__
    log = logging.getLogger(filename)
    return log.info(*args)


def warn(*args):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    # Get the filename
    filename = mod.__name__
    log = logging.getLogger(filename)
    return log.warn(*args)


def error(*args):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    # Get the filename
    filename = mod.__name__
    log = logging.getLogger(filename)
    return log.error(*args)


def crit(*args):
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    # Get the filename
    filename = mod.__name__
    log = logging.getLogger(filename)
    return log.critical(*args)
