#!/usr/bin/env python
import sys
import urllib
import re
import sqlite3
import time
import os

def current_dir():
    name=sys.path[0]
    if os.path.isdir(name):
        return name
    elif os.path.isfile(name):
        return os.path.dirname(name)
    else:
        raise Exception("Invalid path")

def db_row_to_dict(row):
    keys=row.keys()
    size=len(row)
    d={}
    for i in range(size):
        d[keys[i]]=row[i]
    return d

class Translate:
    API='http://dict-co.iciba.com/api/dictionary.php?w='
    DATA=current_dir()+'/words'

    def __init__(self):
        if not os.path.isfile(self.DATA):
            self.initDb()
        self.connectDb()

    def __del__(self):
        self.conn.close()

    def translate(self,word):
        row=self.getFromDb(word)
        #not found in db, then fetch from web
        if not row:
            trans=self.getFromWeb(word)
            if not trans:
                return False
            row={'word':word.decode('utf-8'),'create_time':int(time.time()),'last_time':int(time.time()),'hits':0,'trans':trans.decode('utf-8')}
            self.addWord(row)
        self.increaseHit(word)
        return row

    def connectDb(self):
        self.conn=sqlite3.connect(self.DATA)
        self.conn.row_factory=sqlite3.Row

    def initDb(self):
        self.connectDb()
        c=self.conn.cursor()
        c.execute("CREATE TABLE words (word varchar(32), hits int, create_time int, trans varchar(500), last_time int)");
        self.conn.commit()
        self.conn.close()
            
    def getFromDb(self,word):
        c=self.conn.cursor()
        c.execute('SELECT * FROM words WHERE word=?',(word,))
        result=c.fetchone()
        if result:
            result=db_row_to_dict(result)
        return result
            
    def getFromWeb(self,word):
        content=self.getWebContent(word)
        return self.parse(content)

    def getWebContent(self,word):
        fh=urllib.urlopen(self.API+word)
        content=fh.read()
        return content

    def addWord(self,row):
        c=self.conn.cursor()
        c.execute('INSERT INTO words ('+','.join(row.keys())+') VALUES('+','.join(['?']*len(row))+')',tuple(row.values()))
        self.conn.commit()

    def increaseHit(self,word):
        c=self.conn.cursor()
        c.execute('UPDATE words SET hits=hits+1 WHERE word=?',(word,))
        self.conn.commit()

    def parse(self,content):
        acc=re.findall(re.compile(r"<acceptation>(.*?)</acceptation>",re.S),content)
        if not acc:
            return None
        else:
            return "\n".join(acc[0:3])

if __name__=='__main__':
    t=Translate()
    if len(sys.argv)<2:
        raise Exception("Invalid param")
    r = t.translate(sys.argv[1])
    print r['trans']
