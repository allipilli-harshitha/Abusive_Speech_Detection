#!/usr/bin/env python
# coding: utf-8
#packages 
import pandas as pd
import numpy as np
from pandas import ExcelWriter, ExcelFile
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.stem.snowball import SnowballStemmer
import string
from nltk.stem import WordNetLemmatizer
nltk.download('averaged_perceptron_tagger')
from collections import defaultdict
from nltk.corpus import wordnet

#packages for database connections
import mysql.connector as mc
from mysql.connector import Error
from mysql.connector import MySQLConnection
import time

#packages for vosk and flask
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import wave
import os
import ast
from flask import Flask, render_template
from flask_mysql_connector import MySQL
import time
#import MySQLdb

#database connectivity
app = Flask(__name__)
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DATABASE'] = 'abusive_words'
app.config['MYSQL_PASSWORD'] = 'password'
mysql = MySQL(app)

#required functions
def connect():
    """connect to mysql database"""
    conn = None
    try:
        conn = mysql.connection #MySQLdb.connect("localhost","root","28@PvB28","abusive_words")
        return conn
    except Error as e:
        print(e)

#func for checking list of words in database
def check_list(conn, wds):
    try:
        #st_time = time.time()
        qry = "select distinct * from abusive where"
        for w in wds:
            t = w
            if len(w) > 5:
                t = w[:5]
            qry += " abusive_wrds like \'"+t+"%\' or"
        qry = qry[:-3]
        qry += ";"
        #print(qry)
        cursor = conn.cursor()
        cursor.execute(qry)
        row = cursor.fetchall()
        if row is None or len(row) == 0 or len(wds) == 0:
            return 0, []
        else:
            return 1, [row] 
        
    except Error as e:
        print(e)
    finally :
        #print(time.time()-st_time)
        pass

#for closing the conncetion
def close_the_connection(conn):
    try:
        conn.close()
        #print("connection is closed")
    except Error as e:
        print(e)

#for text cleaning
def remove_punct(text):
    s =set(['"','(',')','.',',','-','<','>','/','\',%', '\\x', '!','?'])
    no_pnt = "".join([c.lower() for c in text if c not in s])
    return no_pnt

#word tokenizer
def tknz_text(text):
    return word_tokenize(text)
    
#after tokenization, we have to remove stop words
def remove_stopwords(text):
    stopword = nltk.corpus.stopwords.words('english')
    tp = ["as","bone","hello","bon","bit","nig","fu","moth","mother","mot","mind","but","nut","crack","who","screw","nasty","fat","fag","skank","horn","big","fist","rap","dum","per","boot","boo","in","int","fioot","ball","wan","kiss","dog","ban","bang","puss","got","goto","mast","cam","foot","piece ","pieceof","pie","hand","hob","eat","hook","whack","upthe","up","blow","spa","span","fast","god","go","bull","no","easy","jack"]
    stopword.extend(tp)
    text = [word for word in text if word not in stopword]
    
    return text

#function for stemming
def stmng(wrds):
    stemmer = SnowballStemmer("english")
    res = []
    for w in wrds:
        res.append(stemmer.stem(w))
    return res 

CHUNK = 1024
@app.route('/')
def index():
  return render_template('index.html')

audio_path = 'C:/Users/HARSHI/Desktop/sukshi project/__downloads/'
#audio_path = 'C:/Users/HARSHI/Downloads/'

#delete audio files after processing stt and tc
def delete():
    global audio_path
    #loc = "/home/veera/Downloads/"
    lst = os.listdir(audio_path)
    for i in lst:
        if i.endswith('.wav'):
            os.remove(audio_path+i)

l=[]
# speech to text process and backend process
@app.route('/record/')
def my_link():

    time.sleep(15)
    c = '0' + '.wav'
    counter  = 0
    conn = connect()
    model = Model("vosk-model-small-en-in-0.4")
    pth = os.listdir(audio_path)
    while(c in pth):
        wf = wave.open(audio_path +'/'+ c, 'rb')
        rec = KaldiRecognizer(model, wf.getframerate())
        while True:
            data = wf.readframes(CHUNK)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                pass
        dict = ast.literal_eval(rec.FinalResult()) #changing the string to dictionary
        print(c)
        #print(dict["text"])
        s = dict["text"]
        print(s)
        
        #Text classification starts
        temp = remove_punct(s)
        temp = tknz_text(temp)
        temp = remove_stopwords(temp)
        temp = stmng(temp)
        #for removing punctions
        puncs =set(['"','(',')','.',',','-','<','>','/','\',%', '\\x', '!','?',"'",'s'])
        temp2= []
        for i in temp:
            if i[0].isalpha() == True:
                temp2.append(i)        

        #for removing spaces
        temp1 = []
        for i in temp2:
            if i not in ("", '', " ",' '):
                temp1.append(i)
               
        print(temp1)
        fg, word = check_list(conn, temp1)
        if fg == 1:
            print("Abusive Detected")
        else:
            print("Normal Text")
        print()
        
        #close_the_connection(conn)
        time.sleep(0.01)
        counter = counter + 1
        c = '0' + ' ' + '(' + str(counter) + ')' + '.wav'
        pth = os.listdir(audio_path)
        #print(pth, "-->", c)
        time.sleep(5)
    try:
    	delete()
    except:
    	return render_template('index.html')
    return render_template('index.html')

if __name__ == '__main__':
  app.run(debug=True)
