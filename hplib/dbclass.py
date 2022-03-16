import decimal
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlparse

def formatval(val):
    if val == None:
        return 'NULL'
    if isinstance(val, (int, float, decimal.Decimal)):
        return str(val)
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d %H:%M:%S')

    return '"%s"' % str(val).replace('"', "'")


class dbClass(object):

    def __init__(self, host, dbname, user, passwd):
        self.engine = create_engine(f"mysql+pymysql://{user}:{passwd}@{host}/{dbname}")
        self.engine.connect()
        self.session = sessionmaker(bind=self.engine)()

        self.test = 0
        self.debug = 0

    @classmethod  # Inititate like this: db = dbClass.from_inifile( 'db.ini' )
    def from_inifile(cls, inifilename, section='database'):
        from configparser import ConfigParser
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
            print( 'Warning: dbClass.query sql parameter should start with SELECT. Use .execute instead\n', sql)
        resultset = self.engine.execute(sql)
        for row_mapping in resultset.mappings().all():
            yield(dict(row_mapping))
        else:
            yield from () # Interesting construction to make sure query always returns a generator

    def execute(self, sql, *params):
        if sql.strip().lower().startswith('select'):
            print( 'Warning: dbClass.execute sql parameter should not start with SELECT. Use .query instead\n', sql)
        if params:
            sql = sql % tuple([str(s).replace('\\', '\\\\').replace("'", r"\'").replace('"', r'\"') for s in params])
        return self._execute(sql)


    def _execute(self, sql):
        if self.debug:
            print(sql)
        for statement in sqlparse.split(sql):
            if statement:
                self.engine.execute(statement.replace('%','%%'), params=None)

    def lookup(self, table, conditions, outfields):
        whereclause = ''
        for key in conditions.keys():
            if not whereclause:
                whereclause = 'WHERE `%s`="%s" ' % (key, conditions[key])
            else:
                whereclause += 'AND `%s`="%s" ' % (key, conditions[key])
        if type(outfields) == type(''):
            what = outfields
        elif type(outfields) == type([]):
            what = ','.join(outfields)

        try:
            res = self.first('SELECT %s FROM %s %s' % (what, table, whereclause))
        except StopIteration:
            return None
        if type(outfields) == type(''):
            return res[outfields]
        else:
            return tuple([res[outf] for outf in outfields])

    def select(self, table, conditions) -> Generator[int, None, None]:
        whereclause = ''
        for key in conditions.keys():
            if not whereclause:
                whereclause = 'WHERE `%s`="%s" ' % (key, conditions[key])
            else:
                whereclause += 'AND `%s`="%s" ' % (key, conditions[key])

        yield from self.query('SELECT * FROM %s %s' % (table, whereclause))

    def insert(self, table, dict, ignore=False):
        keys = ','.join(['%s' % key for key in dict.keys()])
        values = ','.join([formatval(val) for val in dict.values()])
        ignore_string = ignore and ' IGNORE' or ''
        sql = 'INSERT%s INTO %s (%s) VALUES (%s)' % (ignore_string, table, keys, values)
        if self.test:
            if not self.debug:
                print(sql)
        else:
            self.execute(sql)
        return self.last_insert_id()

    def last_insert_id(self):
        return self.first('SELECT LAST_INSERT_ID() as id')['id']

    def update(self, table, wheredict, valuedict, ignore=False):
        valueclause = ','.join(['`%s`=%s' % (key, formatval(valuedict[key])) for key in valuedict.keys()])
        whereclause = ' AND '.join(['`%s`="%s"' % (key, wheredict[key]) for key in wheredict.keys()])
        ignore_keyword = 'IGNORE ' if ignore else ''

        sql = 'UPDATE %s%s SET %s WHERE %s' % (ignore_keyword, table, valueclause, whereclause)

        if self.test:
            if not self.debug:
                print(sql)
        else:
            self.execute(sql)

    def updateinsert(self, table, lookupdict, insertdict):
        lookupfield = list(lookupdict.keys())[0]
        id = self.lookup(table, lookupdict, lookupfield)
        if not id:
            id = self.insert(table, insertdict)
        else:
            self.update(table, lookupdict, insertdict)
        return id

    def delete(self, table, wheredict):
        whereclause = ' AND '.join(['`%s`="%s"' % (key, wheredict[key]) for key in wheredict.keys()])
        sql = 'DELETE FROM %s WHERE %s' % (table, whereclause)
        if self.test:
            if not self.debug:
                print(sql)
        else:
            self.execute(sql)

    def commit(self):
        self.session.commit()
