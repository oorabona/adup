import argparse
import hashlib
import os
from datetime import datetime, timezone
from operator import and_

import sqlalchemy as sa
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql.expression import ClauseElement, Executable

from adup.exceptions import NoFileInDatabase

from .utils import debug, getMatchingConditions, str2bool

# We need to have it global so we can use it every where
# and still use it as a context variable.
last_seen = datetime.now(timezone.utc)


class InsertIntoAsSelect(Executable, ClauseElement):
    inherit_cache = False

    def __init__(self, table, select):
        self.table = table
        self.select = select


@compiles(InsertIntoAsSelect)
def visit_insert_into_as_select(element, compiler, **kw):
    return "INSERT INTO {} {}".format(
        # The following just throws some weird _compiler_dispatch error
        # compiler.process(element.table, asfrom=True, **kw),
        element.table.__tablename__,
        compiler.process(element.select, **kw),
    )


class CreateTableAsSelect(Executable, ClauseElement):
    inherit_cache = False

    def __init__(self, table, select):
        self.table = table
        self.select = select


@compiles(CreateTableAsSelect)
def visit_create_table_as_select(element, compiler, **kw):
    return "CREATE TABLE {} AS {}".format(
        # The following just throws some weird _compiler_dispatch error
        # compiler.process(element.table, asfrom=True, **kw),
        element.table.__tablename__,
        compiler.process(element.select, **kw),
    )


Base = declarative_base()

Session = sessionmaker(
    autoflush=True,
    autocommit=False,
)

# mapper_registry = registry()
# Base = mapper_registry.generate_base()


class Files(Base):
    __tablename__ = "files"

    name = sa.Column(sa.String, primary_key=True)
    path = sa.Column(sa.String, primary_key=True)
    size = sa.Column(sa.Integer, index=True, nullable=False)
    hash = sa.Column(sa.String, index=True, nullable=False)
    hash4k = sa.Column(sa.String, index=True, nullable=False)
    mtime = sa.Column(sa.DateTime, index=True, nullable=False)
    last_seen = sa.Column(sa.DateTime, index=True, nullable=False)

    def __repr__(self):
        return f"Files({self.name!r}, {self.path!r}, {self.size!r}, {self.hash!r}, {self.mtime!r}, {self.last_seen!r})"


class Duplicates(Base):
    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, primary_key=True)
    path = sa.Column(sa.String, primary_key=True)
    size = sa.Column(sa.Integer, index=True, nullable=False)
    hash = sa.Column(sa.String, index=True, nullable=False)
    hash4k = sa.Column(sa.String, index=True, nullable=False)
    mtime = sa.Column(sa.DateTime, index=True, nullable=False)
    selected = sa.Column(sa.Boolean, index=True, nullable=False)

    def __repr__(self):
        return f"Duplicates({self.id!r}, {self.name!r}, {self.path!r}, {self.size!r}, {self.hash!r}, {self.mtime!r}, {self.selected!r})"


# build a model class with a specific table name
# kudos https://www.easydevguide.com/posts/dynamic_table
def get_duplicates_model(conditions):
    tablename = "duplicates_%s" % conditions  # dynamic table name
    class_name = "Duplicates%s" % conditions  # dynamic class name
    Model = type(
        class_name,
        (Duplicates,),
        {
            "__tablename__": tablename,
        },
    )
    return Model


def create_engine(backend, config):
    if backend == "sqlite":
        db = config.get("sqlite", "db")
        backendURI = "sqlite+pysqlite:///%s" % db
    else:
        raise NotImplementedError("Backend %s is not implemented" % backend)

    # Get all items from sa section
    backendOptions = config.items("sqlalchemy")

    # Convert dict of lists to dict of strings
    kwargs = dict(backendOptions)

    # Make sure each option has the correct type
    for key, value in kwargs.items():
        if value.isdigit():
            kwargs[key] = int(value)
        else:
            try:
                kwargs[key] = str2bool(value)
            except argparse.ArgumentTypeError:
                kwargs[key] = value

    debug("Using backend {} with options {}".format(backendURI, kwargs))
    # Create engine with 'future' always enabled :)
    kwargs.update({"future": True})
    engine = sa.create_engine(backendURI, **kwargs)
    Session.configure(bind=engine)
    return engine


def check_same_file(hash4k, size):
    # Check if the first 4K resembles another file in our DB with same properties
    with Session() as session:
        try:
            result = session.query(Files).filter(Files.hash4k == hash4k, Files.size == size).first()
        finally:
            session.close()
        if result:
            debug("File is the same as %s" % result)
            return True
        else:
            return False


def updatedb(root, file, stat, **kwargs):
    # Create a session
    with Session() as session:
        # Get file full path
        fullpath = os.path.join(root, file)
        debug("Updating information for file %s :" % fullpath)

        # Compute SHA256 hash for file
        sha256_hash = hashlib.sha256()
        hash4k = None
        first_4k = True
        is_same_file = False
        with open(fullpath, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                if first_4k:
                    # Check if the first 4K resembles another file in our DB with same properties
                    # If so, we can skip the rest of the file
                    hash4k = sha256_hash.hexdigest()
                    is_same_file = check_same_file(hash4k, stat.st_size)
                    if kwargs.get("always_full_hash") is False and (is_same_file or kwargs.get("only_first_4k")):
                        break
                    else:
                        first_4k = False
                        continue

        # Convert mtime to datetime
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

        # Add file to DB
        try:
            hash = sha256_hash.hexdigest()
            if hash4k is None:
                hash4k = hash

            insert_stmt = sa.dialects.sqlite.insert(Files).values(
                name=file, path=root, size=stat.st_size, hash=hash, hash4k=hash4k, mtime=mtime, last_seen=last_seen
            )

            update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=[Files.name, Files.path],
                set_=dict(size=stat.st_size, hash=hash, hash4k=hash4k, mtime=mtime, last_seen=last_seen),
            )

            session.execute(update_stmt)
            session.commit()
            debug("File added to DB")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def initdb(backend, force):
    if force:
        print("Dropping all tables")
        Base.metadata.drop_all(backend)

        # Remove all duplicates tables
        listOfConditions = getMatchingConditions("every")
        for conditions in listOfConditions:
            joinCondition = "_".join(conditions)
            DuplicatesModel = get_duplicates_model(joinCondition)
            DuplicatesModel.__table__.drop(backend, checkfirst=True)

        with backend.connect() as conn:
            # with conn.begin():   # Optional: start a transaction
            # Run VACUUM to free up space
            conn.execute(sa.text("VACUUM"))

    print("Creating all tables")
    Base.metadata.create_all(backend)


def analyzeDuplicates(conditions):
    # Create a session
    with Session() as session:
        session.begin()
        try:
            # Do we have files in our database ?
            result = session.query(Files).first()
            if result is None:
                raise NoFileInDatabase("No file in database, please run updatedb first")
        except Exception:
            session.rollback()
            raise

        stmt = sa.lambda_stmt(
            lambda: sa.select(
                sa.func.row_number().over().label("id"),
                *[c for c in Files.__table__.c if c.name not in ["last_seen"]],
                sa.sql.expression.literal(False).label("selected"),
            )
        )

        files = Files.__table__
        duplicates = sa.orm.aliased(Files)
        onclause = [files.c.path != duplicates.path]
        for condition in conditions:
            if condition == "samesize":
                onclause.append(files.c.size == duplicates.size)
            elif condition == "samehash":
                onclause.append(files.c.hash == duplicates.hash)
            elif condition == "samehash4k":
                onclause.append(files.c.hash4k == duplicates.hash4k)
            elif condition == "samemtime":
                onclause.append(files.c.mtime == duplicates.mtime)
            elif condition == "samename":
                onclause.append(files.c.name == duplicates.name)
            else:
                raise ValueError("Condition %s is not supported" % condition)

        stmt = (
            stmt.select_from(files.join(duplicates, sa.and_(*onclause), isouter=False))
            .group_by(*[c for c in Files.__table__.c if c.name not in ["last_seen"]])
            .order_by(Files.name, Files.size, Files.mtime, Files.hash, Files.hash4k)
        )

        # join conditions with _
        # they are already sorted so we just need to concatenate them
        joinedConditions = "_".join(conditions)

        try:
            # Get appropriate table name
            Duplicates = get_duplicates_model(joinedConditions)
            engine = session.get_bind()
            # drop table first
            # we need to close the session before dropping the table to prevent locking
            # https://docs.sa.org/en/14/faq/metadata_schema.html
            session.close()
            Duplicates.__table__.drop(engine, checkfirst=True)
            # Create table to maintain correct DDL from Duplicates definition
            # otherwise we would loose indexes and constraints
            Duplicates.__table__.create(engine)
            # Populate table with INSERT INTO SELECT FROM statement
            session.begin()
            session.execute(InsertIntoAsSelect(Duplicates, stmt))
            session.commit()

            # Get duplicates count
            duplicatesCount = session.query(Duplicates).count()
            # Get duplicates total size
            duplicatesSize = session.query(sa.func.sum(Duplicates.size)).scalar()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close_all()

    return duplicatesCount, duplicatesSize


def markDuplicates(conditions, operation, which, name, path):
    results = {}
    # Create a session
    with Session() as session:
        session.begin()
        try:
            for condition in conditions:
                joinCondition = "_".join(condition)
                # Get appropriate table name
                Duplicates = get_duplicates_model(joinCondition)
                # Update duplicates table
                if operation == "select":
                    value = True
                elif operation == "unselect":
                    value = False
                else:
                    raise ValueError("Operation %s is not supported" % operation)

                if which == "all":
                    sq = sa.select(Duplicates.id)
                    if name is not None and path is None:
                        sq = sq.where(Duplicates.name.op("GLOB")(name))
                    elif path is not None and name is None:
                        sq = sq.where(Duplicates.path.op("GLOB")(path))
                    elif path is not None and name is not None:
                        sq = sq.where(and_(Duplicates.path.op("GLOB")(path), Duplicates.name.op("GLOB")(name)))
                elif which == "older":
                    condSQL = sa.select(
                        Duplicates.id, Duplicates.name, sa.func.min(Duplicates.mtime).label("comp")
                    ).group_by(Duplicates.name)
                    if name is not None and path is None:
                        condSQL = condSQL.where(Duplicates.name.op("GLOB")(name))
                    elif path is not None and name is None:
                        condSQL = condSQL.where(Duplicates.path.op("GLOB")(path))
                    elif path is not None and name is not None:
                        condSQL = condSQL.where(
                            and_(Duplicates.path.op("GLOB")(path), Duplicates.name.op("GLOB")(name))
                        )
                    sq = session.query(Duplicates.id).select_from(condSQL).where(Duplicates.mtime == sa.column("comp"))
                elif which == "newer":
                    condSQL = sa.select(
                        Duplicates.id, Duplicates.name, sa.func.max(Duplicates.mtime).label("comp")
                    ).group_by(Duplicates.name)
                    if name is not None and path is None:
                        condSQL = condSQL.where(Duplicates.name.op("GLOB")(name))
                    elif path is not None and name is None:
                        condSQL = condSQL.where(Duplicates.path.op("GLOB")(path))
                    elif path is not None and name is not None:
                        condSQL = condSQL.where(
                            and_(Duplicates.path.op("GLOB")(path), Duplicates.name.op("GLOB")(name))
                        )
                    sq = session.query(Duplicates.id).select_from(condSQL).where(Duplicates.mtime == sa.column("comp"))
                elif which == "larger":
                    condSQL = sa.select(
                        Duplicates.id, Duplicates.name, sa.func.max(Duplicates.size).label("comp")
                    ).group_by(Duplicates.name)
                    if name is not None and path is None:
                        condSQL = condSQL.where(Duplicates.name.op("GLOB")(name))
                    elif path is not None and name is None:
                        condSQL = condSQL.where(Duplicates.path.op("GLOB")(path))
                    elif path is not None and name is not None:
                        condSQL = condSQL.where(
                            and_(Duplicates.path.op("GLOB")(path), Duplicates.name.op("GLOB")(name))
                        )
                    sq = session.query(Duplicates.id).select_from(condSQL).where(Duplicates.size == sa.column("comp"))
                elif which == "smaller":
                    condSQL = sa.select(
                        Duplicates.id, Duplicates.name, sa.func.min(Duplicates.size).label("comp")
                    ).group_by(Duplicates.name)
                    if name is not None and path is None:
                        condSQL = condSQL.where(Duplicates.name.op("GLOB")(name))
                    elif path is not None and name is None:
                        condSQL = condSQL.where(Duplicates.path.op("GLOB")(path))
                    elif path is not None and name is not None:
                        condSQL = condSQL.where(
                            and_(Duplicates.path.op("GLOB")(path), Duplicates.name.op("GLOB")(name))
                        )
                    sq = session.query(Duplicates.id).select_from(condSQL).where(Duplicates.size == sa.column("comp"))
                elif which == "empty":
                    sq = sa.select(Duplicates.id).where(Duplicates.size == 0)
                    if name is not None and path is None:
                        sq = sq.where(Duplicates.name.op("GLOB")(name))
                    elif path is not None and name is None:
                        sq = sq.where(Duplicates.path.op("GLOB")(path))
                    elif path is not None and name is not None:
                        sq = sq.where(and_(Duplicates.path.op("GLOB")(path), Duplicates.name.op("GLOB")(name)))
                else:
                    raise ValueError("Which '%s' is not supported" % which)

                # Update duplicates table and set 'selected' column
                session.execute(Duplicates.__table__.update().where(Duplicates.id.in_(sq)).values(selected=value))

                session.commit()

                # Get selected repartition
                selectedRepartition = (
                    session.query(Duplicates.selected, sa.func.count(Duplicates.selected), sa.func.sum(Duplicates.size))
                    .group_by(Duplicates.selected)
                    .all()
                )
                results[joinCondition] = selectedRepartition
        except Exception:
            session.rollback()
            raise
        finally:
            session.close_all()

    return results


def listDuplicates(operation, conditions, hideColumns):
    # Create a session
    with Session() as session:
        session.begin()
        try:
            all_queries = []
            for condition in conditions:
                joinCondition = "_".join(condition)
                # Get appropriate table name
                Duplicates = get_duplicates_model(joinCondition)
                # Get duplicates but without `id` and `selected` columns
                if operation == "selected":
                    sq = sa.select(
                        *[c for c in Duplicates.__table__.c if c.name not in ["id", "selected", *hideColumns]]
                    ).where(
                        Duplicates.selected == True  # noqa E712
                    )
                elif operation == "unselected":
                    sq = sa.select(
                        *[c for c in Duplicates.__table__.c if c.name not in ["id", "selected", *hideColumns]]
                    ).where(
                        Duplicates.selected == False  # noqa E712
                    )
                else:
                    raise ValueError("Operation %s is not supported" % operation)

                all_queries.append(sq)

            # Union all queries without duplicates :)
            results = session.execute(sa.union(*all_queries).order_by("name", "path")).all()
            columns = results[0].keys() if results else None
        except Exception:
            session.rollback()
            raise
        finally:
            session.close_all()

    return columns, results


# Show Duplicates
# Show detailed information about a file name or path
# given its status on each condition.
def showDuplicates(listOfConditions, name, path):
    # Create a session
    with Session() as session:
        session.begin()
        try:
            all_queries = []
            for condition in listOfConditions:
                joinCondition = "_".join(condition)
                # Get appropriate table name
                Duplicates = get_duplicates_model(joinCondition)
                # Get duplicates but without `id` column
                sq = sa.select(
                    sa.sql.expression.literal(joinCondition).label("condition"),
                    *[c for c in Duplicates.__table__.c if c.name not in ["id"]],
                )
                if name is not None and path is None:
                    sq = sq.where(Duplicates.name == name)
                elif path is not None and name is None:
                    sq = sq.where(Duplicates.path == path)
                elif path is not None and name is not None:
                    sq = sq.where(and_(Duplicates.path == path, Duplicates.name == name))

                all_queries.append(sq)

            # Union all queries without duplicates :)
            results = session.execute(sa.union_all(*all_queries).order_by("name", "path")).all()
            columns = results[0].keys() if results else None
        except Exception:
            session.rollback()
            raise
        finally:
            session.close_all()

    return columns, results


def refreshdb():
    # Create a session
    with Session() as session:
        session.begin()
        try:
            # Count number of files before
            nbFilesBefore = session.query(Files).count()
            stmt = sa.delete(Files).filter(Files.last_seen < last_seen)
            session.execute(stmt)

            # Count number of files after
            nbFilesAfter = session.query(Files).count()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close_all()

    return nbFilesBefore, nbFilesAfter
