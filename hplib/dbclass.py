""" Class to for easy operations on MySql database"""
import decimal
from datetime import datetime
from typing import Generator
from configparser import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlparse


def formatval(val):
    if val is None:
        return 'NULL'
    if isinstance(val, (int, float, decimal.Decimal)):
        return str(val)
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d %H:%M:%S')

    return f'''"{str(val).replace('"', "'")}"'''


class dbClass:
    """ Class to for easy operations on MySql database"""

    def __init__(self, host, dbname, user, passwd):
        self.engine = create_engine(f"mysql+pymysql://{user}:{passwd}@{host}/{dbname}")
        self.engine.connect()
        self.session = sessionmaker(bind=self.engine)()

        self.test = 0
        self.debug = 0

    @classmethod  # Inititate like this: db = dbClass.from_inifile( 'db.ini' )
    def from_inifile(cls, inifilename, section='database'):
        inifile = ConfigParser()
        inifile.read(inifilename)
        params = tuple(inifile.get(section, param) for param in ['dbhost', 'dbname', 'dbuser', 'dbpass'])
        return cls(*params)

    def first(self, sql: str):
        return next(self.query(sql))

    def query(self, sql: str) -> Generator:
        if self.debug:
            print(sql)
        if not sql.strip().lower().startswith('select'):
            print('Warning: dbClass.query sql parameter should start with SELECT. Use .execute instead\n', sql)
        resultset = self.engine.execute(sql.replace('%', '%%'))
        for row_mapping in resultset.mappings().all():
            yield dict(row_mapping)
        yield from ()  # Interesting construction to make sure query always returns a generator

    def execute(self, sql, *params):
        if sql.strip().lower().startswith('select'):
            print('Warning: dbClass.execute sql parameter should not start with SELECT. Use .query instead\n', sql)
        if params:
            print('PARAMS', params)
            sql = sql % tuple([str(s).replace('\\', '\\\\').replace("'", r"\'").replace('"', r'\"') for s in params])
        return self._execute(sql)

    def _execute(self, sql):
        if self.debug:
            print(sql)
        for statement in sqlparse.split(sql):
            if statement:
                self.engine.execute(statement.replace('%', '%%'), params=None)

    def lookup(self, table, conditions, outfields):
        whereclause = ''
        for key in conditions.keys():
            if not whereclause:
                whereclause = f'WHERE `{key}`="{conditions[key]}" '
            else:
                whereclause += f'AND `{key}`="{conditions[key]}" '
        what = ','.join(outfields) if isinstance(outfields, list) else outfields

        try:
            res = self.first(f'SELECT {what} FROM {table} {whereclause}')
        except StopIteration:
            return None
        if isinstance(outfields, str):
            return res[outfields]
        return tuple([res[outf] for outf in outfields])

    def select(self, table, conditions=None) -> Generator[int, None, None]:
        whereclause = ''
        if conditions:
            for key in conditions.keys():
                if not whereclause:
                    whereclause = f'WHERE `{key}`="{conditions[key]}" '
                else:
                    whereclause += f'AND `{key}`="{conditions[key]}" '

        yield from self.query(f'SELECT * FROM {table} {whereclause}')

    def insert(self, table, field_dict, ignore=False):
        keys = ','.join([f'{key}' for key in field_dict.keys()])
        values = ','.join([formatval(val) for val in field_dict.values()])
        ignore_string = ' IGNORE' if ignore else ''
        sql = f'INSERT{ignore_string} INTO {table} ({keys}) VALUES ({values})'
        if self.test:
            if not self.debug:
                print(sql)
        else:
            self.execute(sql)
        return self.last_insert_id()

    def last_insert_id(self):
        return self.first('SELECT LAST_INSERT_ID() as id')['id']

    def update(self, table, wheredict, valuedict, ignore=False):
        valueclause = ','.join([f'`{key}`={formatval(valuedict[key])}'for key in valuedict.keys()])
        whereclause = ' AND '.join([f'`{key}`="{wheredict[key]}"' for key in wheredict.keys()])
        ignore_keyword = 'IGNORE ' if ignore else ''

        sql = f'UPDATE {ignore_keyword}{table} SET {valueclause} WHERE {whereclause}'

        if self.test:
            if not self.debug:
                print(sql)
        else:
            self.execute(sql)

    def updateinsert(self, table, lookupdict, insertdict):
        lookupfield = list(lookupdict.keys())[0]
        record_id = self.lookup(table, lookupdict, lookupfield)
        if not record_id:
            record_id = self.insert(table, insertdict)
        else:
            self.update(table, lookupdict, insertdict)
        return record_id

    def delete(self, table, wheredict):
        whereclause = ' AND '.join([f'`{key}`="{wheredict[key]}"' for key in wheredict.keys()])
        sql = f'DELETE FROM {table} WHERE {whereclause}'
        if self.test:
            if not self.debug:
                print(sql)
        else:
            self.execute(sql)

    def commit(self):
        self.session.commit()
