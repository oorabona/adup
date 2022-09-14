# adup - Advanced Duplicate Finder

`adup` is a tool to find duplicate files in a directory tree. It is written in Python for use with Python 3.6 or later.

`adup` is a command line tool. It can be used to find duplicate files in a directory tree. It can also be used to operate on the duplicate files, e.g. to move, copy or delete them.

## Installation

`adup` is available on PyPI and can be installed with `pip`:

```bash
pip install adup
```

## Usage

Once installed, you must `init` its configuration file.

```bash
adup init
```

If you are running it as a logging user (whether `root` or any user with login shell), this will create a configuration file in `~/.config/adup/adup.conf` by default.
If you are running it from a `daemon`-ized environment (e.g. `cron`), it will create a configuration file in `/etc/adup/adup.conf`.

You can edit this file to change the default configuration during creation or after using this command.

```bash
adup init -c /path/to/adup.conf
```


### Finding duplicate files
