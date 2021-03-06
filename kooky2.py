import string
import cPickle
import pickle
import time
import os
import types
import db
import testValue
from mod_python import Cookie, apache,util #@UnresolvedImport


def myCookies(req,action,data,dbname,selectedHost):
        
    # here I manage the browser cookies as well as the mysql kooky table
    # the browser stores an id and a dbanme
    # the kooky table has records storing lots of data identified by the cookieID
    # this enables each host to have their own information and thus multiple hosts may use the same installation
    # ONLY ONE DB CAN BE ACCESSED PER BROWSER/HOST OR KOOKY DATA WILL BE MIXED UP
    #
    # the username and password for accessing the kookyDB will be the dbname 
    # a user by that name with that password must have insert,update privileges to the kooky db
    
#     util.redirect(req,"testValue.py/testvalue?test=action:"+str(action)+" dbname:"+str(dbname))
    #~ action="save"
    
    cookieID=''
    kookyDB=''
    cookieData={}
    qupdate="no"
    kookyTable='_kooky'
    qinsert="no"
    
    # assign a name for the cookie
    # the name of the cookie is the 
    # name of the web dir + '_id'
    apacheConfig=req.get_config()
    rootPath=apacheConfig['PythonPath'][11:-2]
    cookieName=rootPath.split("/")[-1]+'_id'
    remoteHost=req.get_remote_host()
    
    # get the browser cookie
    getCookie=Cookie.get_cookies(req)
    
    try:
        # get the current kooky values
        cookieID,kookyDB=getCookie[cookieName].value.split()
        
        # if I passed a dbname update the data only
        if dbname:
            newCookie = Cookie.Cookie(cookieName, cookieID+' '+dbname)
            newCookie.expires = time.time() + 31449600 # extend expires by one year
            Cookie.add_cookie(req, newCookie)
            kookyDB=dbname
            
        # if no name passed then just get the stored data
        else:
            cookieData['kookyID']=cookieID
            cookieData['kookyDB']=kookyDB
            
#         util.redirect(req,"testValue.py/testvalue?test="+repr(kookyDB))
        
    except:
        # no cookie found so create one
        for i in time.localtime()[:6]:
            if len(str(i))==1:
                    digit='0'+str(i)
            else:
                    digit=str(i)
            cookieID=cookieID+digit
    
        newCookie = Cookie.Cookie(cookieName, cookieID+' '+dbname)
        newCookie.expires = time.time() + 31449600 # one year
        Cookie.add_cookie(req, newCookie)
    
#     util.redirect(req,"testValue.py/testvalue?test=kookyDB:"+str(kookyDB)+" dbname:"+str(dbname))
    # above is all about browser cookies
    #*********************************************
        
    
    #*********************************************
    # below is all about the 3t kooky table
    
    if action=='':     
        # just used for initial startup
        # just return the kookyID
        kookyData=cookieID
        
    elif action=='db':
        # just return the dbname for getting the config
        kookyData=kookyDB #kookyData['kookyDB']
    #
    #*********************************************
        
    #*********************************************
    #
    # Insert or Update kooky data
    elif action=='save':
        
        # see if a kooky is already stored
        #

        q='select `_kooky`.`kookyData` from `'+str(dbname)+"`.`_kooky`" \
        ' where `_kooky`.`_kookyID`="'+str(cookieID)+'"'
        try:
            kookyData=db.dbConnect(selectedHost,kookyDB,q,1)
        except:
            kookyData=''
        
#         d=data['results']
#         d3=d[0]
#         util.redirect(req,"testValue.py/testvalue?test="+repr((d3))+'---'+str(kookyData))  
        ##+'___'+str(kookyData))

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
            kookyData="%s",remoteHost="%s" where _kookyID=%s'%(pData,remoteHost,cookieID)
            
            #~ util.redirect(req,"testValue.py/testvalue?test="+"kooky"+repr(q))
            qupdate=db.dbConnect(selectedHost,kookyDB,q,-1)
            
        # Insert new kooky
        else:
            q='insert into `'+str(dbname)+'`.`_kooky` \
            (_kookyID,kookyData,remoteHost) values (%s,"%s","%s")'%(cookieID,pData,remoteHost)

            #~ util.redirect(req,"testValue.py/testvalue?test="+"kooky"+repr(kookyDB))
            
            qinsert=db.dbConnect(selectedHost,dbname,q,-1)
#             util.redirect(req,"testValue.py/testvalue?test="+"kooky2"+repr(qinsert))
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
           ' where _kookyID="'+cookieID+'"' ##%s'%(kookyID)
           
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

