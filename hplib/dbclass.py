import decimal
from datetime import datetime

import pymysql  # pip3 install pymysql
from pymysql import constants
from sqlalchemy import create_engine

def formatval( val ):
    if val==None:
        return 'NULL'
    if isinstance( val, ( int, float, decimal.Decimal ) ):
        return str(val)
    if isinstance( val, datetime):
        return val.strftime( '%Y-%m-%d %H:%M:%S')
        
    return '"%s"' % str(val).replace('"',"'")

class dbClass(object):
    
    def __init__(self, host, dbname, user, passwd ):
        self._dbhost = host
        self._dbname = dbname
        self._dbuser = user
        self.__dbpass = passwd

        self.db = pymysql.connect(host=host, user=user, passwd=passwd, db=dbname, client_flag=constants.CLIENT.MULTI_STATEMENTS)
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)

        self.test = 0
        self.debug = 0
        self.engine = None

    def sql_alchemy_engine(self):
        if not self.engine:
            self.engine = create_engine(f"mysql+pymysql://{self._dbuser}:{self.__dbpass}@{self._dbhost}/{self._dbname}")
            self.engine.connect()
        return self.engine

    @classmethod # Inititate like this: db = dbClass.from_inifile( 'db.ini' )
    def from_inifile( cls, inifilename, section='database' ):
        from configparser import ConfigParser
        inifile = ConfigParser()
        inifile.read( inifilename )
        params = tuple( inifile.get( section, param ) for param in ['dbhost', 'dbname', 'dbuser', 'dbpass'])
        return cls( *params )

    def execute(self,sql,*params):
        if params:
            sql = sql % tuple([str(s).replace('\\','\\\\').replace("'",r"\'").replace('"',r'\"') for s in params])
        return self._execute(sql)

    def _execute( self, sql ):
        if self.debug:
            print( sql )
        if (sql.strip().lower().startswith('select')):
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        else:
            return self.cursor.execute(sql)
    
    def lookup( self, table, conditions, outfields ):
        whereclause = ''
        for key in conditions.keys():
            if not whereclause:
                whereclause = 'WHERE `%s`="%s" ' % (key, conditions[key])
            else:
                whereclause += 'AND `%s`="%s" ' % (key, conditions[key])
        if type(outfields)== type(''):
            what = outfields
        elif type(outfields) == type([]):
            what = ','.join( outfields )
    
        res = self.execute( 'SELECT %s FROM %s %s' % (what, table, whereclause) )
        if len(res)>0:
            if type(outfields)== type(''):
                return res[0][outfields]
            else: 
                return tuple( [res[0][outf] for outf in outfields] )
        else:
            return None
            
    def select( self, table, conditions ):
        whereclause = ''
        for key in conditions.keys():
            if not whereclause:
                whereclause = 'WHERE `%s`="%s" ' % (key, conditions[key])
            else:
                whereclause += 'AND `%s`="%s" ' % (key, conditions[key])
    
        return self.execute( 'SELECT * FROM %s %s' % (table, whereclause) )

            
    def insert( self, table, dict, ignore=False ):
        keys = ','.join( ['%s' % key for key in dict.keys()] )
        values = ','.join( [formatval(val) for val in dict.values()] )
        ignore_string = ignore and ' IGNORE' or ''
        sql = 'INSERT%s INTO %s (%s) VALUES (%s)' % (ignore_string, table, keys,values)
        if self.test:
            if not self.debug:
                print( sql )
        else:
            self.execute( sql )
        return self.last_insert_id()

    def last_insert_id(self):
        return self.execute( 'SELECT LAST_INSERT_ID() as id' )[0]['id']
        
    def update( self, table, wheredict, valuedict, ignore=False ):
        valueclause = ','.join( ['`%s`=%s' % (key,formatval(valuedict[key])) for key in valuedict.keys()] )
        whereclause = ' AND '.join( ['`%s`="%s"' % (key,wheredict[key]) for key in wheredict.keys()] )    
        ignore_keyword = 'IGNORE ' if ignore else ''
    
        sql = 'UPDATE %s%s SET %s WHERE %s' % (ignore_keyword, table, valueclause, whereclause )
    
        if self.test:
            if not self.debug:
                print( sql )
        else:
            self.execute( sql )
        
    def updateinsert( self, table, lookupdict, insertdict ):
        lookupfield = list(lookupdict.keys())[0]
        id = self.lookup( table, lookupdict, lookupfield )
        if not id:
            id = self.insert( table, insertdict )
        else:
            self.update( table, lookupdict, insertdict )
        return id
            
    def delete( self, table, wheredict ):
        whereclause = ' AND '.join( ['`%s`="%s"' % (key,wheredict[key]) for key in wheredict.keys()] )
        sql = 'DELETE FROM %s WHERE %s' % (table, whereclause)
        if self.test:
            if not self.debug:
                print( sql)
        else:
            self.execute( sql )
    
    def commit( self ):
        self.db.commit()

