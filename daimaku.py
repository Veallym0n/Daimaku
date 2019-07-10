#!/bin/python
#coding:utf8
import ast
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import pandas
import astor
import json
import sqlite3
import readline
from tabulate import tabulate
from traceback import print_exc
from pdb import set_trace as st

pandas.set_option('display.max_rows',None)
pandas.set_option('display.max_colwidth',2048)

def rand(node=None):
    return os.urandom(8).encode('hex')


class Daimaku(object):

    def __init__(self, file_or_dir=[]):
        self.mode = 'fancy_grid'              # 展示模式
        self.file_list = file_or_dir
        self.codebase = {}
        self.CodeCache = {}
        self.parse_code()
        self.codedb = sqlite3.connect(':memory:')
        self.codedb.text_factory = lambda x:x.decode('utf8')
        self.codedb.row_factory = lambda cursor,row:dict((col[0], row[idx]) for idx, col in enumerate(cursor.description))
        for db in self.codebase:
            pandas.DataFrame(self.codebase[db]).to_sql(db, self.codedb, index=False)


    def parse_code(self):
        for fn in self.file_list:
            try:
                astcode = ast.parse(open(fn).read())
                self._main(fn, astcode)
                pretty('green','[ OK  ]',fn)
            except Exception,e:
                pretty('red', '[ ERR ]',fn,e)


    def _main(self, fn, astc):
        for node in ast.walk(astc):
            node.codeid = getattr(node,'codeid',rand())
            if isinstance(node, ast.AST):
                for subnode in ast.iter_child_nodes(node):
                    subnode.parent = node
                    subnode.codeid = rand(node)
                    self.CodeCache[subnode.codeid] = subnode
                    if isinstance(subnode,ast.FunctionDef):
                        self.codebase['functions'] = self.codebase.get('functions',[])+[
                                {'id':subnode.codeid, 'func_name':subnode.name,'line':subnode.lineno,
                                  'file':fn,'deco':','.join([astor.to_source(i).strip() for i in subnode.decorator_list]),
                                  'args':','.join([astor.to_source(i).strip() for i in subnode.args.args]),'argslen':len(subnode.args.args)
                                 }
                                ]
                    elif isinstance(subnode,ast.ClassDef):
                        self.codebase['classes'] = self.codebase.get('classes',[])+[
                                {'id':subnode.codeid, 'class_name':subnode.name,'line':subnode.lineno,
                                  'file':fn,'deco':','.join([astor.to_source(i).strip() for i in subnode.decorator_list]),
                                  'extends':','.join([astor.to_source(i).strip() for i in subnode.bases])
                                 }
                                ]
                    elif isinstance(subnode,ast.Call):
                        self.codebase['calls'] = self.codebase.get('calls',[])+[
                                {'id': subnode.codeid, 'func_name': astor.to_source(subnode.func).strip(),'line':subnode.lineno,
                                  'file':fn,'argslen':len(subnode.args)
                                 }
                                ]
                    elif isinstance(subnode,ast.ImportFrom):
                        self.codebase['imports'] = self.codebase.get('import',[])+[
                                {'id':subnode.codeid, 'line':subnode.lineno, 'file':fn, 
                                 'name':subnode.names[0].name, 'asname':subnode.names[0].asname,
                                 'module':subnode.module
                                }
                                ]
                    elif isinstance(subnode, ast.Str):
                        self.codebase['strings'] = self.codebase.get('strings',[])+[
                                {'id':subnode.codeid, 'line':subnode.lineno, 'file':fn,
                                 'string':subnode.s}
                                ]

    def query(self, sql):
        cur = self.codedb.cursor()
        data = pandas.DataFrame(cur.execute(sql).fetchall())
        cur.close()
        return data

    def makeQuery(self, sql):
        if self.mode == 'psql':
            print tabulate(DMK.query(sql.strip()),headers='keys',tablefmt='psql')
        elif self.mode == 'json':
            print DMK.query(sql.strip()).to_json(orient='index')
        else:
            print tabulate(DMK.query(sql.strip()),headers='keys',tablefmt=self.mode)


    def add_function(self, filename):
        import imp
        udf = imp.load_source('_',filename)
        udf.run(self)

def pretty(c,*msgs):
    colordict = {'green':'\033[1;32m%s\033[0m',
                 'red'  :'\033[1;31m%s\033[0m'}
    sys.stderr.write(colordict.get(c,'%s') % ' '.join(map(str,msgs))+'\n')


def stdin_factory():
    while True:
        sql = raw_input('sql> ')
        try:
            if sql.lower().startswith('select '):
                DMK.makeQuery(sql.strip())
            elif sql.lower().startswith('add udf'):
                DMK.add_function(sql.rsplit()[-1])
            elif sql.lower().startswith('set mode'):
                DMK.mode = sql.rsplit()[-1]
            elif sql in ('exit','quit'):
                break
            elif not sql.strip():
                pass
            else:
                pretty('red','unknown query statment')
        except Exception,e:
            pretty('red','[ Err ]',e)


if __name__=='__main__':
    DMK = Daimaku(map(lambda x:x.strip(),sys.stdin.readlines()))
    sys.stdin = open('/dev/tty')
    sys_args = dict(zip(sys.argv[1:len(sys.argv):2],sys.argv[2:len(sys.argv):2]))

    DMK.add_function(os.path.dirname(os.path.abspath(__file__))+'/udf/sample.py')
    DMK.mode = sys_args.get('-mode','psql')
    DMK.sql = sys_args.get('-sql','')

    if DMK.sql!= '':
        DMK.makeQuery(DMK.sql.strip())
        sys.exit(1)
    stdin_factory()
