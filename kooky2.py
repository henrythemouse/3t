import string
import cPickle
import pickle
import time
import os
import types
import db
import testValue
from mod_python import Cookie, apache,util


def myCookies(req,action,data,kookyDB,selectedHost):
        
    #~ util.redirect(req,"testValue.py/testvalue?test="+action+" "+kookyDB)
    #~ action="save"
    
    kookyID=''
    kookyData={}
    qupdate="no"
    kookyTable='kooky'
    qinsert="no"
    
    # assign a name for the cookie
    # the name of the cookie is the 
    # name of the web dir + '_id'
    apacheConfig=req.get_config()
    rootPath=apacheConfig['PythonPath'][11:-2]
    kookyName=rootPath.split("/")[-1]+'_id'
    remoteHost=req.get_remote_host()
    
    # get the browser cookie
    kooky=Cookie.get_cookies(req)

        
    try:
        # get the current kooky values
        kookyID,kookyDB2=kooky[kookyName].value.split()
        
        # if I passed a dbname update the data only
        if kookyDB:
            kooky = Cookie.Cookie(kookyName, kookyID+' '+kookyDB)
            kooky.expires = time.time() + 31449600 # one year
            Cookie.add_cookie(req, kooky)
        # if no name passed then just get the stored data
        else:
            kookyData['kookyID']=kookyID
            kookyData['kookyDB']=kookyDB2
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(kookyDB2))
    except:
        # no cookie found so create one
        for i in time.localtime()[:6]:
            if len(str(i))==1:
                    digit='0'+str(i)
            else:
                    digit=str(i)
            kookyID=kookyID+digit
    
        kooky = Cookie.Cookie(kookyName, kookyID+' '+kookyDB)
        kooky.expires = time.time() + 31449600 # one year
        Cookie.add_cookie(req, kooky)
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(kookyID))
    #
    #
    #*********************************************
        
    
    #*********************************************
    if action=='':     
        # just used for initial startup, when lastUpdate is enabled
        # just return the kookyID
        kookyData=kookyID
        
    elif action=='db':
        # just return the dbname for getting the config
        kookyData=kookyData['kookyDB']
    #
    #*********************************************
        
    #*********************************************
    #
    # Insert or Update kooky data
    elif action=='save':
        
        # see if a kooky is already stored
        #

        q='select kookyData from '+str(kookyTable)+ \
        ' where _kookyID='+str(kookyID)

        kookyData=db.dbConnect(selectedHost,kookyDB,q,1)
        
        # trap an unsuccessful query
        if kookyData<1:
            kookyData=''
        else:
            kookyData="found"
            
        # pickle the kooky data        
        #~ pData=cPickle.dumps(data)
        pData=pickle.dumps(data)
        
        # Here I have to remove all the " characters
        # in the qtext variable or the query that
        # saves qtext wont work. I put them back in
        # when I retrieve qtext for use.
        pData=string.replace(pData,'"','*****')
        pData=repr(pData)
        pData=pData[1:-1]
        
        # Update the kooky
        if kookyData:
            
            # when a prev kooky is found update it
            q='update '+str(kookyTable)+' set \
            kookyData="%s",remoteHost="%s" where _kookyID=%s'%(pData,remoteHost,kookyID)
            
            #~ util.redirect(req,"testValue.py/testvalue?test="+"kooky"+repr(q))
            qupdate=db.dbConnect(selectedHost,kookyDB,q,-1)
            
        # Insert new kooky
        else:
            q='insert into '+str(kookyTable)+' \
            (_kookyID,kookyData,remoteHost) values (%s,"%s","%s")'%(kookyID,pData,remoteHost)

            qinsert=db.dbConnect(selectedHost,kookyDB,q,-1)
            #~ util.redirect(req,"testValue.py/testvalue?test="+"kooky"+repr(qinsert))
    #
    #
    #*********************************************
    
    #*********************************************
    #    
    # Get the kooky data from the mysql db
    elif action=='get':
        
        # see if a kooky is already stored
        #
        q='select kookyData from '+str(kookyTable)+\
           ' where _kookyID="'+kookyID+'"' ##%s'%(kookyID)
           
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(q))
           
        kookyData=db.dbConnect(selectedHost,kookyDB,q,1)
        
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(kookyData)+'---'+q)

        if kookyData:
            kookyData=kookyData[0]
            # I had to remove all " characters in the qtext
            # variable before I could save it to the db.
            # So, here I put them back where they belong.
            kookyData=string.replace(kookyData,'*****','"')
            #~ kookyData=cPickle.loads(kookyData)
            kookyData=pickle.loads(kookyData)
            kooky=kookyData
        else:
            kooky=0
    #
    #
    #*********************************************

    #*********************************************
    #    
    return kookyData
    #
    #
    #*********************************************

