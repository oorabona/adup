# adup - Advanced Duplicate Finder

`adup` is a tool to find duplicate files in a directory tree. It is written in Python for use with Python 3.8 or later.

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

If the configuration file already exists, it will not be overwritten. You can use the `-f` option to force the creation of a new configuration file.

```bash
adup init -f
```

Once the configuration file is created, you need to initialize the database that will serve the purpose of finding duplicates.

```bash
adup initdb
```

This will create a database file in the directory given in the configuration file.
At the moment only `sqlite` is supported as a database backend.

If you need to reset the database, you can use the `-f` option to force the recreation of the database.

```bash
adup initdb -f
```

### Configuration file

The configuration file is a classic INI-style configuration file.

```ini
# Comments should start with a # and must be full lines
[global]

# At least one backend must be choosen, for now only sqlite is supported.
# This must be something SQLAlchemy understands.
backend = sqlite

# If you want to specify common paths to include and exclude, you can do it here.
# You can also specify them on the command line.
# Note : excluding paths is done after including paths.
[paths]
include[] =
exclude[] =

# Specific parameters for Alchemy should be set here.
[sqlalchemy]
echo = False

# The following options are used by the sqlite3 backend.
[sqlite]

# The database file to use.
db = /path/to/db.sqlite3
```

### Finding duplicate files

To find duplicate files, you must first initialize the database with the `initdb` command.

```bash
adup initdb
```

This will create a database file in the directory given in the configuration file.

Once the database is initialized, you can find duplicate files with the `updatedb` command.

```bash
adup updatedb
```

This will find duplicate files in the directory tree and store them in the database.
You can specify the paths to include and exclude with the `-i` and `-e` options.

```bash
adup updatedb -i /path/to/include -e /path/to/exclude
```

You can even add multiple paths to include and exclude.

```bash
adup updatedb -i /path/to/include1 -i /path/to/include2 -e /path/to/exclude1 -e /path/to/exclude2
```

You can also specify the paths to include and exclude in the configuration file.
If you need to specify more than one path, you can specify one path each line using `include[]` or `exclude[]` respectively.

```ini
[paths]
include[] = /path/to/include1
include[] = /path/to/include2
exclude[] = /path/to/exclude1
exclude[] = /path/to/exclude2
```

> Note that the paths specified on the command line will complete (and *NOT* override) the paths specified in the configuration file.

Also, note that exclusion paths are applied *after* inclusion paths.
So basically, it means the following:

* If you specify a path to include, it will be included *ONLY* if it is not excluded.
* If you specify a subpath to exclude, the siblings of this subpath will be included *ONLY* if they are not excluded.
* If you specify a subpath to include, the siblings of this subpath will be excluded *ONLY* if they are not included.

E.g:

```ini
[paths]
include[] = /path/to/include
exclude[] = /path/to/include/subpath
```

In this case, `/path/to/include/subpath` will be excluded, but `/path/to/include` will be included.
Moreover `/path/to/include/sibling1` and `/path/to/include/sibling2` will be included.

On the contrary, if you specify:

```ini
[paths]
include[] = /path/to/include
exclude[] = /path/to/include
```

Then `/path/to/include` will be excluded, and `/path/to/include/subpath` will be excluded too.

And finally if you specify:

```ini
[paths]
include[] = /path/to/include/subpath
exclude[] = /path/to/exclude
```

Then `/path/to/exclude` will be excluded, and `/path/to/include/subpath` will be included.

### Operating on duplicate files

You have four types of operations you can perform on files:

1. Analyze: to get the most information about the duplicate files.
2. List/show: to have a view on the duplicate files and their details.
3. Mark: to mark duplicate files as to be operated on.
4. File operations: to operate on the marked files (e.g: `rm`, `cp` and `mv` like operations).

#### Analyze

To analyze duplicate files, you can use the `analyze` command.

```bash
adup analyze
```

This will analyze the duplicate files and store the results in the database.

Duplicates are analyzed by comparing different aspects of their metadata.
The following aspects are compared:

* File `size`
* File modification time (`mtime`)
* File SHA256 hash (`hash`)
* File SHA256 hash on the first 4K of the file (`hash4k`)
* File name (`name`)

If you want to analyze only a subset of the duplicates, you can use the `-t` option to specify the type of duplicates to analyze.

```bash
adup analyze -t size
```

There are two additional types of comparison:

* `all`: to analyze given a combination of all the above aspects.
* `every`: to analyze every aspect separately.

#### List/show

To list duplicate files, you can use the `list` command.

```bash
adup list
```

This will list all the duplicate files in the database according to what has been `analyze`-d previously.
It reports the following information:

* The `name` of the duplicate file.
* The `size` of the duplicate file.
* The `mtime` of the duplicate file.
* The `hash` of the duplicate file.
* The `hash4k` of the duplicate file.
* The `path` of the duplicate file.

If you want to list only a subset of the duplicates, you can use the `-t` option to specify the type of duplicates to list.

```bash
adup list -t size
```

If you want to hide the `path` column, you can use the `--hide` option.

```bash
adup list --hide path
```

You can also hide multiple columns.

```bash
adup list --hide path --hide hash
```

Listing will give you the overview for all the duplicates whereas showing will give you the details for a specific duplicate.
To show the details of a specific duplicate, you can use the `show` command.

```bash
adup show /path/to/duplicate
```

This will show the details of the duplicate file at `/path/to/duplicate`.
It reports the following information:

* The `name` of the duplicate file.
* The `size` of the duplicate file.
* The `mtime` of the duplicate file.
* The `hash` of the duplicate file.
* The `hash4k` of the duplicate file.
* The `path` of the duplicate file.

If you want to show only a subset of the duplicates, you can filter using either the `-n` (by name) or `-p` (by path) options.

```bash
adup show -n /path/to/duplicate
```

```bash
adup show -p /path/to/duplicate
```

You can combine the two options to filter by both name and path.

```bash
adup show -n /path/to/duplicate -p /path/to/duplicate
```

> Note: these are strict comparisons, so no wildcards are allowed.

Then you will have details for the duplicate file at `/path/to/duplicate` with the name `/path/to/duplicate`.


#### Mark

To mark duplicate files, you can use the `mark` command.

```bash
adup mark
```
