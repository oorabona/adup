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

The default path for the configuration file will eventually depend on the operating system and the presence of a `USER` environment variable. For now, it is always `~/.config/adup/adup.conf`.

> If you are running it as a logging user (whether `root` or any user with login shell), this will create a configuration file in `~/.config/adup/adup.conf` by default.
> If you are running it from a `daemon`-ized environment (e.g. `cron`), you should not have any `USER` environment variable set, it will create a configuration file in `/etc/adup/adup.conf`.

You can edit this file to change the default configuration during creation or after using this command.

```bash
adup init -c /path/to/adup.conf -e /path/to/editor
```

E.g. to create a configuration file in `/etc/adup/adup.conf` and edit it with `vim`:

```bash
adup init -c /etc/adup/adup.conf -e vim
```


### Finding duplicate files
