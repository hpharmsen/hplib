""" Tests for the dbClass module """

import configparser
import os

import pytest

from hplib.dbclass import dbClass


@pytest.fixture
def database():
    config_file = "hplib/db.ini"
    database = dbClass.from_inifile(config_file)
    return database


@pytest.fixture
def table():
    return "test_dbclass"


def test_connnect_to_db():
    config_file = "hplib/db.ini"
    config = configparser.ConfigParser()
    assert os.path.isfile(config_file)
    config.read(config_file)

    database = dbClass(*config["database"].values())
    assert database is not None, "Could not connect to database"
    return database


def test_create_db(database, table):
    query = f"DROP TABLE IF EXISTS {table}"
    database.execute(query)
    query = f"CREATE TABLE {table} (name VARCHAR(20), age INT)"
    database.execute(query)
    assert True


def test_insert_value(database, table):
    database.insert(table, {"name": "cheddar", "age": 3})
    database.insert(table, {"name": "kees", "age": 4})
    assert True


def test_first(database: dbClass, table):
    rec = database.first(f"select name from {table} where age=4")
    assert rec == {"name": "kees"}


def test_select_one(database: dbClass, table: str):
    res = database.select(table, {"name": "cheddar"})
    assert next(res) == {"name": "cheddar", "age": 3}


def test_select_all(database: dbClass, table: str):
    res = database.select(table, {})
    assert next(res) == {"name": "cheddar", "age": 3}
    assert next(res) == {"name": "kees", "age": 4}


def test_select_on_multiple_constraints(database: dbClass, table: str):
    res = database.select(table, {"name": "cheddar", "age": 3})
    assert next(res) == {"name": "cheddar", "age": 3}


def test_multiple_statments(database: dbClass, table: str):
    queries = f'''insert into {table} (name, age) values ("brie",5); 
                  insert into {table} (name, age) values ("camembert",6)'''
    database.execute(queries)
    res = database.select(table, {"age": 6})
    assert next(res) == {"name": "camembert", "age": 6}


def test_lookup(database: dbClass, table: str):
    brie_age = database.lookup(table, {"name": "brie"}, "age")
    assert brie_age == 5


def test_lookup2(database: dbClass, table: str):
    brie_age = database.lookup(table, {"name": "brie"}, ["age", "name"])
    assert brie_age == (5, "brie")


def test_last_insert_id(database):
    last_insert_id = database.last_insert_id()
    print(last_insert_id)
    assert True


def test_update(database: dbClass, table: str):
    database.update(table, {"name": "cheddar"}, {"age": 4})
    age = database.lookup(table, {"name": "cheddar"}, "age")
    assert age == 4


def test_updateinsert(database: dbClass, table: str):
    database.updateinsert(table, {"name": "cheddar"}, {"age": 8})
    age = database.lookup(table, {"name": "cheddar"}, "age")
    assert age == 8


def test_updateinsert2(database: dbClass, table: str):
    database.updateinsert(table, {"name": "roquefort"}, {"name": "roquefort", "age": 8})
    age = database.lookup(table, {"name": "roquefort"}, "age")
    assert age == 8


def test_delete(database: dbClass, table: str):
    database.delete(table, {"age": 8})
    assert len(list(database.select(table))) == 3


def test_cleanup(database: dbClass, table: str):
    query = f"DROP TABLE {table}"
    database.execute(query)
