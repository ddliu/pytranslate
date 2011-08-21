#!/usr/bin/env python
import sys
import urllib
import re
import sqlite3
import datetime,time
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
    API='http://dict-co.iciba.com/api/dictionary.php?w=' # The translate api
    DATA=current_dir()+'/words' #Data file

    def __init__(self):
        """ Init db connection"""
        if not os.path.isfile(self.DATA):
            self.initDb()
        self.connectDb()

    def __del__(self):
        """Release resource"""
        self.conn.close()

    def loop(self):
        """Main loop"""
        while True:
            #Enter word or command(command start with ".")
            word=raw_input('-'*30+"\nEnter word or command:")
            word=word.strip()
            if not word:
                break

            if word.startswith('.'):
                if word == '.help':
                    self.cmd_help()
                elif word == '.hot':
                    self.cmd_hot(30)
                elif word == '.exit':
                    break
                else:
                    print "Invalid command"
                continue

            #Translate word
            word=word.decode('utf-8')
            row=self.translate(word)
            if not row:
                print "%s not found in dictionary" % (word)
            else:
                print row['trans']
                if row['hits']>0:
                    print "%s hit(s) since %s, last time is %s" % (row['hits'],datetime.datetime.fromtimestamp(row['create_time']),datetime.datetime.fromtimestamp(row['last_time']))

    def generate_help(self):
        """Generate help message from methods"""
        for m in [m for m in dir(self) if m.startswith('cmd_')]:
            cmd=m.replace('cmd_','')
            print '.'+cmd
            doc=eval('self.'+m+'.__doc__')
            if doc:
                print doc
            print ""

    def cmd_help(self):
        """Print help messages"""
        print "Simple translate program(English => Chinese)"
        print "Version 0.1"
        print "Author: Dong <ddliuhb@gmail.com>"
        print "Commands:"
        print self.generate_help()

    def cmd_hot(self,limit=30):
        """List words by top hits"""
        words=self.getHotFromDb(limit)
        for word in words:
            print "%s (%s)" % (word['word'],word['hits'])

    def cmd_exit(self):
        """Exit"""
        sys.exit(0)

    def translate(self,word):
        """Translate one word, if not found in DB, we need to fetch it from internet"""
        row=self.getFromDb(word)
        #not found in db, then fetch from web
        if not row:
            trans=self.getFromWeb(word)
            if not trans:
                return False
            #Note word need to be decoded here(bitcode to unicode)
            row={'word':word.decode('utf-8'),'create_time':int(time.time()),'last_time':int(time.time()),'hits':0,'trans':trans.decode('utf-8')}
            self.addWord(row)

        #Increase hit of this word
        self.increaseHit(word)
        return row

    def connectDb(self):
        self.conn=sqlite3.connect(self.DATA)
        self.conn.row_factory=sqlite3.Row

    def initDb(self):
        """Create db and init db schema"""
        self.connectDb()
        c=self.conn.cursor()
        c.execute("CREATE TABLE words (word varchar(32), hits int, create_time int, trans varchar(500), last_time int)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_word ON words(word)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_hits ON words(hits)")
        self.conn.commit()
        self.conn.close()
            
    def getFromDb(self,word):
        """ Get word info from db"""
        c=self.conn.cursor()
        c.execute('SELECT * FROM words WHERE word=?',(word,))
        result=c.fetchone()
        if result:
            result=db_row_to_dict(result)
        return result
            
    def getFromWeb(self,word):
        """ Get translate from internet and parse it"""
        content=self.getWebContent(word)
        return self.parse(content)

    def getWebContent(self,word):
        """ Get translate from internet"""
        fh=urllib.urlopen(self.API+urllib.quote(word.encode('utf-8')))
        content=fh.read()
        return content

    def addWord(self,row):
        """ Add word to db """
        c=self.conn.cursor()
        c.execute('INSERT INTO words ('+','.join(row.keys())+') VALUES('+','.join(['?']*len(row))+')',tuple(row.values()))
        self.conn.commit()

    def increaseHit(self,word):
        """ Increase hit of word """
        c=self.conn.cursor()
        c.execute('UPDATE words SET hits=hits+1,last_time=? WHERE word=?',(int(time.time()),word,))
        self.conn.commit()
    
    def getHotFromDb(self,limit):
        """ Get top words from db """
        c=self.conn.cursor()
        c.execute("SELECT * FROM words WHERE hits >0 ORDER BY hits DESC LIMIT ?",(limit,))
        return c.fetchall()

    def parse(self,content):
        """ Parse translate content """
        acc=re.findall(re.compile(r"<acceptation>(.*?)</acceptation>",re.S),content)
        if not acc:
            return None
        else:
            return "\n".join(acc[0:3])

if __name__=='__main__':
    t=Translate()
    t.loop()
