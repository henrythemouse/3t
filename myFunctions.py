import string
import db
import os
import os.path
import shutil
import kooky2
import MySQLdb #@UnresolvedImport
import index

from mod_python import util #@UnresolvedImport

# use this call to check variable values
# util.redirect(req,"testValue.py/testvalue?test="+repr(qresult))

def dogout(req):

#    util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form))
    config=getConfig(req,req.form['dbname'].value)
    action=req.form['action'].value

    try:
        req.form['dogout'].value
        data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])
        data['username']=''
        data['userpass']=''

        kookied=kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])
        #~ util.redirect(req,"../testValue.py/testvalue?test="+repr(kookied))

    except:
        pass

    if action=='15':
        parameter='?media='+req.form['media']
    else:
#        parameter='?media='+req.form['media']
        parameter='?action='+req.form['action']

    util.redirect(req,"../index.py"+parameter)

def dogin(req):

#    util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form))
    config=getConfig(req,req.form['dbname'].value)
    cancelClicked=''
    action=req.form['action'].value

    try:
        req.form['dogin'].value
        username=req.form['dogleg'].value
        userpass=req.form['cattail'].value
    except:
        try:
            cancelClicked=req.form['cancel'].value
            username=''
            userpass=''
        except:
            username=''
            userpass=''


    # test for a valid login
    loginAccepted=1
    try:
        dbconnection = MySQLdb.connect(host=config['selectedHost'],user=username,passwd=userpass,db=config['dbname'])
    except:
        loginAccepted=0
    try:
        # for transactional tables like innodb
        dbconnection.commit()
    except:
        pass        
    try:
        dbconnection.close()
    except:
        pass


#     util.redirect(req,"../testValue.py/testvalue?test="+repr(error))

    # if it's a good login then save it to the kooky table
    if loginAccepted:
        data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])

        data['username']=username
        data['userpass']=userpass

        kookied=kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])

    if cancelClicked:
        if int(action)>90:
            action="3"
        parameter='?action='+action
    else:
        if loginAccepted:
            if int(action)>90:
                parameter='?action=3'
            elif action=='15':
                parameter='?media='+req.form['media']
            else:
#                parameter='?media='+req.form['media']
                parameter='?action='+req.form['action']
        else:
            parameter='?popup=98&amp;action=98'

    util.redirect(req,"../index.py"+parameter)

def getConfig(req,dbname):
    config={}
    config['configError']='NO'
    config['dbname']=dbname
    config['selectedHost']='localhost'
    config['configTable']='_config'
    config['login']=''
    primaries=[]
    apacheConfig=req.get_config()
    rootPath=apacheConfig['PythonPath'][11:-2]

#     util.redirect(req,"testValue.py/testvalue?test="+repr(config))
    
    try:

        try:
            # get the stored config values from the _config table
            q="select * from `"+config['dbname']+"`.`"+config['configTable']+"`"
            configValues=db.dbConnect('localhost',dbname,q,1)
            if configValues==None:
                # no record present, this will require a user/pass that has insert privilegesd 
                # the standard user/pass would be dbname/dbname and by default would only have select privileges.
                # so, this is a bit of a problem requiring the config table to be initialized with one record 
                # or be able to login before having a config. Consequently, this will fail as will any attempt
                # to edit the _config table or any other table util a valid login is accomplished.
                insertq="insert into `"+config['configTable']+"` (`"+dbname+"`) values ('"+dbname+"')"
                recordInsert=db.dbConnect('localhost',dbname,insertq,0)
#             util.redirect(req,"testValue.py/testvalue?test="+repr(insertq))

            q="show columns from `"+dbname+"`.`_config`"
            configCols=db.dbConnect('localhost',dbname,q,0)
            for col in range(1,len(configCols)):
                if configValues[col]==None:
                    value=""
                else:
                    value=configValues[col]
                config[configCols[col][0].strip()]=value.strip()
                            
        except:
            config['configError']='Query failed: '+q

#         util.redirect(req,"testValue.py/testvalue?test="+repr(q))

        # set the table names, item table is same as dbname, cat table will have 2 id columns, media table will have 3 id cols
        try:
            q="show tables from `"+config['dbname']+"`"
            showTables=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisTable in showTables:
                q1="show columns from `"+thisTable[0]+"`"
                qresult=db.dbConnect(config['selectedHost'],config['dbname'],q1,0)
                idColCount=0
                for thisCol in qresult:
                    if thisCol[0][0]=="_":
                        idColCount=idColCount+1
                if idColCount==3:
                    config['mediaTable']=thisTable[0]
                elif idColCount==2:
                    config['catTable']=thisTable[0]
            config['itemTable']=config['dbname']
        except:
            config['configError']='Query failed: '+q+ 'Query failed: '+q1

#         util.redirect(req,"testValue.py/testvalue?test="+repr(q1))
                
        # query mysql for it's values for the itemTable
        try:
            itemCols=[]
            charCols=[]
            q="show columns from `"+config['itemTable']+"`"
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisCol in qresult:
                if 'PRI' in thisCol[3]:
                    config['itemIDfield']=thisCol[0]
                    primaries.append(thisCol[0])
                elif 'blob' in thisCol[1]:
                    config['itemIMGfield']=thisCol[0]
                elif 'char' in thisCol[1]:
                    charCols.append(thisCol[0])
                    itemCols.append(thisCol[0])
                elif thisCol[0][0]!='_':
                    itemCols.append(thisCol[0])
            config['itemShowColumns']=itemCols
            # if not specified use charCols for default itemlist
            if len(charCols)>=3:
                listCols=charCols[:2]
                tableCols=charCols[:4]
        except:
            config['configError']='Query failed: '+q

#         util.redirect(req,"testValue.py/testvalue?test="+repr(config))

        # query mysql for it's values for the catTable
        try:
            catCols=[]
            q="show columns from `"+config['catTable']+"`"
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisCol in qresult:
                if 'PRI' in thisCol[3]:
                    config['catIDfield']=thisCol[0]
                    primaries.append(thisCol[0])
                elif 'text' in thisCol[1]:
                    config['catNoteField']=thisCol[0]
                elif thisCol[0][-1]=="_":
                    config['catInfoColumn']=thisCol[0]
                    catCols.append(thisCol[0])
                elif thisCol[0][0]!='_':
                    catCols.append(thisCol[0])
                    
            config['catShowColumns']=catCols
        except:
            config['configError']='Query failed: '+q
            

        # query mysql for it's values for the mediaTable
        try:
            mediaCols=[]
            q="show columns from `"+config['mediaTable']+"`"
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisCol in qresult:
                if 'PRI' in thisCol[3]:
                    config['mediaIDfield']=thisCol[0]
                    primaries.append(thisCol[0])
                elif "blob" in thisCol[1]:
                    config['mediaBlob']=thisCol[0]
                elif thisCol[0][0]!='_':
                    mediaCols.append(thisCol[0])
            config['mediaShowColumns']=mediaCols
        except:
            config['configError']='Query failed: '+q
            
#         util.redirect(req,"testValue.py/testvalue?test="+repr(config)+"before")

        # populate the supportTables and tableNames config variables
        try:
            config['supportTables']=[]
            config['tableNames']=[]
            for thisTable in showTables:
                config['supportTables'].append(thisTable[0])
                config['tableNames'].append(thisTable[0])
            config['supportTables'].remove(config['itemTable'])
            config['supportTables'].remove(config['catTable'])
            config['supportTables'].remove(config['mediaTable'])
            config['supportTables'].remove('kooky')
            config['supportTables'].remove('_config')
            config['tableNames'].remove('kooky')
            config['tableNames'].remove('_config')
        except:
            config['configError']='Query failed: '+q
            
#         util.redirect(req,"testValue.py/testvalue?test="+repr(config)+"before")
        
        try:
            config['rootPath']=rootPath
            config['primaries']=primaries
            config['dbImagePath']=rootPath+"/images/"
            config['defaultImagePath']=rootPath+"/images/defaults"
            config['catImagePath']=rootPath+"/catimages/"
            config['itemImagePath']=rootPath+"/itemimages/"
            config['mediaPath']=rootPath+"/tmp/"
            config['itemListColumns']=config['itemListColumns'].split()
            config['itemColumns']=config['itemColumns'].split(" ")
            config['catSearchColumns']=config['catSearchColumns'].split()
            config['owner']='owner'
            config['invisible']='filename'
        except:
            config['configError']='Assignments failed'
            
#         util.redirect(req,"testValue.py/testvalue?test="+repr(config)+"after")

        # config defaults
        if not config['theme']:
            config['theme']='default'
        if not config['displayname']:
            config['displayname']=config['dbname']
        if not config['displaylogo']:
            config['displaylogo']='defaultlogo.png'
        if not config['popupbackground']:
            config['popupbackground']=config['displaylogo']
        if not config['selectedHost']:
            config['selectedHost']='localhost'
        if not config['catSortColumn']:
            config['catSortColumn']=config['catIDfield']
        if not config['itemListColumns']:
            config['itemListColumns']=listCols
        if not config['itemColumns']:
            config['itemColumns']=tableCols
        if not config['emailcontact']:
            config['emailcontact']='root@localhost'
#         dbImages(config)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(config)+"after2")

    except:
        config['configError']="configError"

    return config

def dbImages(config):

    # setup the db specific images path, keeping those seperate from program images
    # paving the way for db specific themes
    imagesPath=config['dbImagePath']+config['dbname']+'/'
    
    if os.path.exists(imagesPath):
        pass
    else:
        # create the db images path
        os.mkdir(imagesPath)

    # copy the default file(s) to the db specific dir
    try:
        shutil.copy(config['dbImagePath']+'defaultlogo.png',imagesPath)
    except:
        pass
    
    return

def cat(req):

    config=getConfig(req,req.form['dbname'].value)

    # get the column names and column types for tableName
    cols={}
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],config['catTable'])
    fieldNames=fieldInfo['fieldNames']
    for col in fieldNames:
        try:
            cols[col]=req.form[col].value
        except:
            try:
                cols[col]=req.form[col]
            except:
                pass

    try:                # SAVE clicked
        action=req.form['savebutton.x']
        action='insert'
        cols[config['itemIDfield']]=req.form['itemID'].value
        cols[config['catColumn']]=req.form['system'].value
    except:
        try:            # UPDATE clicked
            action=req.form['updatebutton.x']
            action='update'
            cols[config['catIDfield']]=req.form['catID'].value
        except:
            action='cancel'

#     util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form.list))
    if action !='cancel':

        what=doSql(req,action,cols,config['catIDfield'],config['dbname'],config['catTable'],config['selectedHost'],config['owner'])
        cleanTmp(config)
        
        if what[0]:
            parameter="?error="+what[0]
        else:
            parameter="?action=7"
    else:
        parameter="?action=7"

    util.redirect(req,"../index.py"+parameter)

def item(req):

    config=getConfig(req,req.form['dbname'].value)

    # get the column names and column types for tableName
    cols={}
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],config['itemTable'])
    fieldNames=fieldInfo['fieldNames']
    for col in fieldNames:
        try:
            cols[col]=req.form[col].value
        except:
            try:
                cols[col]=req.form[col]
            except:
                pass

    try:                # buttons pass xy locations, just test for one
        action=req.form['savebutton.x']
        action='insert'
    except:
        try:
            action=req.form['updatebutton.x']
            action='update'
            cols[config['itemIDfield']]=req.form['itemID'].value
        except:
            action='cancel'

    if action !='cancel':

        what=doSql(req,action,cols,config['itemIDfield'],config['dbname'],config['itemTable'],config['selectedHost'],config['owner'])
        cleanTmp(config)
        
#        util.redirect(req,"../testValue.py/testvalue?test="+repr(what))
        if what[0]:
            parameter="?error="+what[0]
        elif action=='insert':
            insertID=what[1]
            parameter="?action=4&amp;item="+str(insertID)
        else:
            parameter="?action=3"
    else:
        parameter="?action=3"

    util.redirect(req,"../index.py"+parameter)

def media(req):

    config=getConfig(req,req.form['dbname'].value)

    # get the column names and column types for tableName
    cols={}
    filename=''
    q=''
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],config['mediaTable'])
    fieldNames=fieldInfo['fieldNames']

    test=[]
    for col in fieldNames:
        try:
            cols[col]=req.form[col].value
        except:
            try:
                cols[col]=req.form[col]
            except:
                pass

    if 'filename' in fieldNames:
        try:
            filename=req.form[config['mediaBlob']].filename
        except:
            pass
        
        # if no filename was passed use the old filename (if there is one) because the file hasn't changed
        if filename=="":
            try:
                q="select `"+config['invisible']+"` from `"+config['mediaTable']+\
                '` where `'+config['mediaTable']+'`.`'+config["mediaIDfield"]+'`'+'="'+req.form['mediaID'].value+'"'
                qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
                cols[config['invisible']]=qresult[0]
            except:
                cols[config['invisible']]=""
        else:
            cols[config['invisible']]=filename
        
    try:                # SAVE clicked
        action=req.form['savebutton.x']
        action='insert'
        #  what table and record to relate to
        cols[config['catIDfield']]=req.form['catID'].value
    except:
        try:            # UPDATE clicked
            action=req.form['updatebutton.x']
            action='update'
            cols[config['mediaIDfield']]=req.form['mediaID'].value
        except:
            action='cancel'

    #  set the realted table, so this returns to the correct data
    tableID=req.form['catID']

#     util.redirect(req,"../testValue.py/testvalue?test="+repr(cols)+repr(filename))

    if action!='cancel':

        what=doSql(req,action,cols,config['mediaIDfield'],config['dbname'],config['mediaTable'],config['selectedHost'],config['owner'])
        cleanTmp(config)
        #        util.redirect(req,"../testValue.py/testvalue?test="+repr(what))

        if what[0]:
            parameter="?error="+what[0]
        else:
#            insertID=what[1]
            parameter="?media="+str(tableID)
    else:
#        try:
#            cancelAction=req.form['cancelAction']
#        except:
#            cancelAction="7"
#        parameter="?action="+cancelAction
        parameter="?media="+str(tableID)

    util.redirect(req,"../index.py"+parameter)

def Imedia(req):

    config=getConfig(req,req.form['dbname'].value)
#    util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form.list))

    # get the column names and column types for tableName
    cols={}
    filename=''
    q=''
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],config['mediaTable'])
    fieldNames=fieldInfo['fieldNames']
    for col in fieldNames:
        if col != fieldInfo['idField']:
            try:
                cols[col]=req.form[col].value
            except:
                try:
                    cols[col]=req.form[col]
                except:
                    pass

    if 'filename' in fieldNames:
        try:
            filename=req.form[config['mediaBlob']].filename
        except:
            pass
            
        # if no filename was passed use the old filename (if there is one) because the file hasn't changed
        if filename=="":
            try:
                q="select "+config['invisible']+" from `"+config['mediaTable']+\
                '` where `'+config['mediaTable']+'`.`'+config["mediaIDfield"]+'`'+'="'+req.form['mediaID'][1:]+'"'
                qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
                cols[config['invisible']]=qresult[0]
            except:
                cols[config['invisible']]=""
        else:
            cols[config['invisible']]=filename

#    util.redirect(req,"../testValue.py/testvalue?test="+repr(cols)+repr(filename)+str(q))

    try:                # SAVE clicked
        action=req.form['savebutton.x']
        action='insert'
        #  what table and record to relate to
        cols[config['itemIDfield']]=req.form['itemID'].value
    except:
        try:            # UPDATE clicked
            action=req.form['updatebutton.x']
            action='update'
            # filter out the item tag
            if req.form['mediaID'][0]=='I':
                cols[config['mediaIDfield']]=req.form['mediaID'][1:]
            else:
                cols[config['mediaIDfield']]=req.form['mediaID'].value
        except:
            action='cancel'


    tableID="I"+req.form['itemID']


    if action!='cancel':
#        util.redirect(req,"../testValue.py/testvalue?test="+repr(cols))##+repr(cols[config['mediaIDfield']]))

        what=doSql(req,action,cols,config['mediaIDfield'],config['dbname'],config['mediaTable'],config['selectedHost'],config['owner'])
        cleanTmp(config)
        
#        util.redirect(req,"../testValue.py/testvalue?test="+repr(what))

        if what[0]:
            parameter="?error="+what[0]
        else:
#            insertID=what[1]
            parameter="?media="+str(tableID)
    else:
        parameter="?action=3"

    util.redirect(req,"../index.py"+parameter)

def support(req):

#     util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form.list))
    
    try:
        dbname=req.form['dbname'].value
    except:
        dbname=req.form['dbname']
        
    config=getConfig(req,dbname)    
    supportTableName=req.form['supportTableName']
    config['supportBlob']='image'
    
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],supportTableName)
    fieldNames=fieldInfo['fieldNames']

    # get the column names and values from the form submission
    # I've changed the method here (only), I parse the form data without regard to the table fieldnames
    # in the other functions (item, cat, and media) I parse using the fieldnames as dic keys
    # I had to do it this way because I couldn't get html multiple select values the other way
    # I'm storing these multi values as a space seperated string, meaning in this case that column names can't have spaces in them.
    # This is all needed just for the _config table which uses multiple select html for column names
    # It could work better for all functions however
    cols={}
    formKeys=req.form.keys()
    for thisKey in formKeys:
        if thisKey in fieldNames:
            try:
                cols[thisKey]=req.form[thisKey].value
            except:
                formString=''
                for thisValue in req.form[thisKey]:
                    formString=formString+" "+(str(thisValue))
                cols[thisKey]=formString

#     util.redirect(req,"../testValue.py/testvalue?test="+repr(cols)+"---")

    if 'filename' in fieldNames:
        try:
            filename=req.form[config['supportBlob']].filename
        except:
            pass
        
        # if no filename was passed use the old filename (if there is one) because the file hasn't changed
        if filename=="":
            try:
                q="select `"+config['invisible']+"` from `"+supportTableName+\
                '` where `'+supportTableName+'`.`_id`'+'="'+req.form['supportID'].value+'"'
                qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
                cols[config['invisible']]=qresult[0]
            except:
                cols[config['invisible']]=""
        else:
            cols[config['invisible']]=filename

    try:                # buttons pass xy locations, just test for one
        action=req.form['savebutton.x']
        action='insert'
    except:
        try:
            action=req.form['updatebutton.x']
            action='update'
            cols[fieldInfo['idField']]=req.form['supportID'].value
        except:
            try:
                req.form['newConfig']
                del cols['newConfig']
                del cols['supportTableName']
                action='insert'
            except:
                action='cancel'

#     util.redirect(req,"../testValue.py/testvalue?test="+repr(action)+"---"+str(cols))

    if action !='cancel':

        what=doSql(req,action,cols,fieldInfo['idField'],dbname,supportTableName,config['selectedHost'],"")

#         util.redirect(req,"../testValue.py/testvalue?test="+repr(what)+"   "+str(config['dbname']))

        if what[0]:
            parameter="?error="+what[0]
#         elif action=='insert':
#             insertID=what[1]
#             parameter="?action=23&amp;item="+str(insertID)
        else:
            if supportTableName=='_config':
                parameter="?action=20"
            elif supportTableName=='_category':
                parameter="?action=23&amp;supportTableName="+supportTableName
            else:
                parameter="?action=23&amp;supportTableName="+supportTableName
    else:
        if supportTableName=='_config':
            parameter="?action=20"
        else:
            parameter="?action=23&amp;supportTableName="+supportTableName
        

    util.redirect(req,"../index.py"+parameter)

def delMedia(req):

    config=getConfig(req,req.form['dbname'].value)
    
    try:
        action=req.form['delMedia'].lower()
    except:
        try:
            action=req.form['cancel'].lower()
        except:
            action='cancel'

    config=getConfig(req,req.form['dbname'])

    itemID=req.form['itemID']
    mediaID=req.form['mediaID']
    selectedHost=config["selectedHost"]
    tableName=config['mediaTable']
    idField=config['mediaIDfield']
    dbname=config['dbname']

#    util.redirect(req,"../testValue.py/testvalue?test="+str(req.form)+"*****"+str(action))
    if action!='cancel':

        # delete the record
        what=doSql(req,"DELETE",mediaID,idField,dbname,tableName,selectedHost,"")
        if what[0]:
            parameter="?error="+what[0]
        else:
#            parameter="?media="+mediaRecord
            parameter="?action=3&amp;item="+str(itemID)
    else:
#        parameter="?media="+mediaRecord
        parameter="?action=3&amp;item="+str(itemID)

    util.redirect(req,"/3t/index.py"+parameter)

def delCat(req):

    config=getConfig(req,req.form['dbname'].value)

    try:
        action=req.form['delCat'].lower()
    except:
        try:
            action=req.form['cancel'].lower()
        except:
            action='cancel'

    config=getConfig(req,req.form['dbname'])

    catID=req.form['catID']
    selectedHost=config["selectedHost"]
    tableName=config['catTable']
    idField=config['catIDfield']
    dbname=config['dbname']
    currentCat=req.form['currentCat']

#    util.redirect(req,"../testValue.py/testvalue?test="+str(req.form)+"*****"+str(action))
    if action!='cancel':

        # delete the record
        what=doSql(req,"DELETE",catID,idField,dbname,tableName,selectedHost,"")
        if what[0]:
            parameter="?error="+what[0]
        else:
#            parameter="?action=8"
            parameter="?action=8&amp;category="+str(currentCat)
    else:
#        parameter="?action=8"
        parameter="?action=8&amp;category="+str(currentCat)

    util.redirect(req,"/3t/index.py"+parameter)

def delItem(req):

    config=getConfig(req,req.form['dbname'].value)
    
    try:
        action=req.form['delItem'].lower()
    except:
        try:
            action=req.form['cancel'].lower()
        except:
            action='cancel'

    config=getConfig(req,req.form['dbname'])

    itemID=req.form['itemID']
    selectedHost=config["selectedHost"]
    tableName=config['itemTable']
    idField=config['itemIDfield']
    dbname=config['dbname']
#    util.redirect(req,"../testValue.py/testvalue?test="+str(req.form)+"*****"+str(action))

    if action!='cancel':

        # delete the record
        what=doSql(req,"DELETE",itemID,idField,dbname,tableName,selectedHost,"")
        if what[0]:
            parameter="?error="+what[0]
        else:
            # tell the routine where to return to, home.
            parameter=''
    else:
        # just go home, where ever that is.
        parameter=''

    util.redirect(req,"/3t/index.py"+parameter)

def delSupport(req):
    
#     util.redirect(req,"../testValue.py/testvalue?test="+str(req.form.list))
    config=getConfig(req,req.form['dbname'].value)
    supportID=req.form['supportID']
    supportTableName=req.form['supportTableName']
#     itemID=req.form['itemID']
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],supportTableName)
    
    try:
        action=req.form['delSupport'].lower()
    except:
        try:
            action=req.form['cancel'].lower()
        except:
            action='cancel'

    config=getConfig(req,req.form['dbname'])

#    util.redirect(req,"../testValue.py/testvalue?test="+str(req.form)+"*****"+str(action))
    if action!='cancel':

        # delete the record
        what=doSql(req,"DELETE",supportID,fieldInfo['idField'],config['dbname'],supportTableName,config["selectedHost"],"")
        
        if what[0]:
            parameter="?error="+what[0]
        else:
#            parameter="?media="+mediaRecord
            parameter="?action=23&amp;supportTableName="+supportTableName
    else:
#        parameter="?media="+mediaRecord
        parameter="?action=23&amp;supportTableName="+supportTableName

    util.redirect(req,"/3t/index.py"+parameter)

def doSql(req,action,cols,idField,dbname,tableName,selectedHost,owner):
    # this handles all insert, update, and delete sql
    # So, if the user is not logged in or doesn't have permission then this will fail
    # the default user (dbname) should only have select permission
#     util.redirect(req,"../testValue.py/testvalue?test="+"doSql"+repr(cols))
    
    error=""
    insertID=''
    config=getConfig(req,req.form['dbname'].value)

    data=kooky2.myCookies(req,'get','',dbname,selectedHost)
    #~ util.redirect(req,"../testValue.py/testvalue?test="+repr(data))

    try:
        username=data['username']
        userpass=data['userpass']
    except:
        pass
    if not username:
        username=dbname
    if not userpass:
        userpass=dbname
#     util.redirect(req,"../testValue.py/testvalue?test="+repr(username)+repr(userpass)+str(dbname))

    # get the column names and column types for tableName
    fieldInfo=getFieldInfo3(req,selectedHost,dbname,tableName)
    fieldNames=fieldInfo['fieldNames']
    fieldTypes=fieldInfo['fieldTypes']

    # insert a new record
    if action=='insert':

        # **********************************************************
        # INSERT - Since newRec HAS a value then this must be an insert query
        # **********************************************************
        #
        setCols=''
        valueTags=''
        setValues=[]
        # For each colname in this table see
        # if the form passed a value - which it
        # does for all editable fields (I think).

        for colname in cols:

            try:
                colvalue=cols[colname]
            except:
                colvalue="skipme"

            # if it's a blob field then don't change that colvalue
            if 'blob' in fieldTypes[colname.lower()]:
                if colvalue:
                    pass
#                     if config['convert2']:
#                         conversion=convertImg(config,colvalue,cols[config['invisible']])
#                         colvalue=conversion[0]
#                         error=conversion[1]
                else:
                    colvalue="skipme"

            # if it's a set field then change that colvalue
            elif 'set(' in fieldTypes[colname.lower()]:
                #~ error='set'
                if type(colvalue)==type([1]):
                    colvalue=string.join(colvalue,',')

            else:
                # Not a blob, so it's not binary.
                if colvalue=='None':
                    colvalue='NULL'
                else:
                    colvalue=quoteHandler(colvalue)
                    colvalue=colvalue.strip()

            # Checking to see if there is a colvalue
            # **************************************
            # Those values set to 'skipme' will remain what they previousely were.
            # Empty values will be skipped because if number fields are empty strings, the query will crash.
            # mysql will insert the defined default value for the skipped fields.
            if colvalue:
                pass
            else:
                colvalue="skipme"
            if colvalue=='skipme':
                pass
            else:
                setCols=setCols+",`"+colname+"`"
                valueTags=valueTags+","+"%s"
                setValues.append(colvalue)

        # if there is an owner field defined insert the username
        if owner in fieldNames:
            setCols=setCols+",`"+owner+"`"
            valueTags=valueTags+","+"%s"
            setValues.append(username)



        setCols="("+setCols[1:]+")"
        valueTags="("+valueTags[1:]+")" #tuple(valueTags)
        setValues=tuple(setValues)

        ########### this works

        q='insert into `'+tableName+'` '+ setCols+" "+ 'values '+valueTags
#         util.redirect(req,"../testValue.py/testvalue?test="+str(q)+repr(setValues))

        try:
            dbconnection = MySQLdb.connect(host=selectedHost,user=username,passwd=userpass,db=dbname)
            xcursor = dbconnection.cursor()

            xcursor.execute(q,(setValues))
            xcursor.execute("SELECT LAST_INSERT_ID()")
            insertID=xcursor.fetchone()[0]
        except:
#            qstr=q.replace('%s','value')
            error='Insert error for '+tableName  +" and user "+str(username)+".\\n\\n Perhaps you are not the owner of this record or are not logged in"
#             error=str(q)+"   "+str(setValues)
#            error=str(q)
        try:
            xcursor.close()
        except:
            pass
        try:
            # for transactional tables like innodb
            dbconnection.commit()
        except:
            pass        
        try:
            dbconnection.close()
        except:
            pass
        ########################


    elif action=='update':

        # *******************************************************************
        # UPDATE - Since newRec DOESN'T have a value then this must be an update query
        # *******************************************************************
        #
        # Because a field may need to be updated to NULL, NULL is used instead
        # of skipme in cases where that might apply - strickly an update concern.
        setCols=''
        idValue=''
        setValues=[]
        # For each colname in this table see
        # if the form passed a value - which it
        # does for all editable fields (I think).

        for colname in fieldNames:

            try:
                if colname==idField:
                    colvalue='skipme'
                    idValue=cols[colname]
                else:
                    colvalue=cols[colname]
            except:
                colvalue="skipme"

            # if it's a blob field then don't change that colvalue
            if 'blob' in fieldTypes[colname.lower()]:
                if colvalue:
                    pass
#                     if config['convert2']:
#                         conversion=convertImg(config,colvalue,cols[config['invisible']])
#                         colvalue=conversion[0]
#                         error=conversion[1]
                else:
                    colvalue="skipme"

            # if it's a set field then change that colvalue
            elif 'set(' in fieldTypes[colname.lower()]:
                if type(colvalue)==type([1]):
                    colvalue=string.join(colvalue,',')

            else:
                # Not a blob, so it's not binary.
                if colvalue==None:
                    colvalue=''
                else:
                    colvalue=quoteHandler(colvalue)
                    colvalue=colvalue.strip()

            # Checking to see if there is a colvalue
            # **************************************
            # Those values set to 'skipme' will remain what they previousely were.
            if colvalue=='skipme':
                pass
            else:
                setCols=setCols+",`"+colname+'`=%s'
                setValues.append(colvalue)

        setCols=setCols[1:]
        setValues=tuple(setValues)

        # if there is an owner field defined, get the owner and check it against current username
        if owner in fieldNames:
            q='select `'+owner+'` from `'+tableName+'` where `'+idField+"`='"+str(idValue)+"'"
                        
            result=db.dbConnect(selectedHost,dbname,q,1)
            #~ util.redirect(req,"../testValue.py/testvalue?test="+repr(result))

            try:
                if result[0]:
                    ownerName=result[0]
                else:
                    ownerName=''
            except:
                ownerName=''
            if ownerName.strip()==username.strip():
                pass
            else:
                username=dbname
                userpass=dbname


        ########### this works
        q="update `"+tableName+"` set "+str(setCols)+" where `"+idField+"`='"+str(idValue)+"'"
#         util.redirect(req,"../testValue.py/testvalue?test="+str(q)+str(setValues))

        try:
            dbconnection = MySQLdb.connect(host=selectedHost,user=username,passwd=userpass,db=dbname)
            cursor = dbconnection.cursor()
            cursor.execute(q,setValues)
#             util.redirect(req,"../testValue.py/testvalue?test="+repr(q)+str(username+" "+userpass+" "+dbname))
        except:
            error="Update error for "+tableName +" and user "+str(username)+".\\n\\n Perhaps you are not the owner of this record or are not logged in.\\n\n Otherwise check that the data you are submitting is valid IAW the database design."
#             error=str(q)+"   "+str(setValues)
        try:
            xcursor.close()
        except:
            pass
        try:
            # for transactional tables like innodb
            dbconnection.commit()
        except:
            pass        
        try:
            dbconnection.close()
        except:
            pass
        ########################

    elif action=="DELETE":
        # *******************************************************************
        # DELETE - The current record
        # *******************************************************************
        #
        error=""

        q="delete from `"+tableName+"` where `"+tableName+"`.`"+idField+"`="+"'"+str(cols)+"'"
        error=""
#        util.redirect(req,"../testValue.py/testvalue?test="+repr(q))

        try:
            dbconnection = MySQLdb.connect(host=selectedHost,user=username,passwd=userpass,db=dbname)
            cursor = dbconnection.cursor()
            cursor.execute(q)
        except:
            error="Delete error for "+tableName  +" and user "+str(username)+".\\n\\n Perhaps you are not the owner of this record or are not logged in.\\n\n Otherwise check that the data you are submitting is valid IAW the database design."

        try:
            xcursor.close()
        except:
            pass
        try:
            # for transactional tables like innodb
            dbconnection.commit()
        except:
            pass        
        try:
            dbconnection.close()
        except:
            pass
        ########################

    return (error,insertID)

def getServerInfo(selectedHost, variableName):
    # get the specifiec server variable and return it
    q='show variables'
    serverVariables=db.dbConnect(selectedHost,'mysql',q,0)
    serverVariable='none'
    if variableName:
        for thisVariable in serverVariables:
            if variableName==thisVariable[0]:
                serverVariable=thisVariable[1]

    return serverVariable

def getFieldInfo3(req,selectedHost,dbname,tableName):

    # get the field names, field types for this table
    # preload some variables
    fieldInfo={}
    fieldTypes={}
    fieldDefaults={}
    fieldNames=[]
    fieldInfo['idField']=''
    fieldInfo['idLoc']=0

    # this function will only work if the table structure
    # used by mysql for the column definition
    # is exactly this (from version 4.0.17):

    # Field - Type - Null - Key - Default - Extra

    # I don't know of a way to verify this or even
    # obtain this information, so I assume it.

    q="show columns from `"+str(tableName)+"`"
    qresult=db.dbConnect(selectedHost,dbname,q,0)

    if qresult>0:
        for thisFieldDefinition in qresult:
            # dictionary of fieldname and fieldTypes
            fieldName=thisFieldDefinition[0]
            fieldNames.append(fieldName)
            fType=thisFieldDefinition[1]
            fDefault=thisFieldDefinition[4]


            # this only recognizes ONE PRI ID field,
            # the last one encountered?
            #
            if 'PRI' in thisFieldDefinition:
                #~ if fieldName[0]=='_':
                fieldInfo['idField']=fieldName

            # why do I lower the field name?
            # for matching purposes
            fieldTypes[fieldName.lower()]=fType
            fieldDefaults[fieldName.lower()]=fDefault

        fieldInfo['fieldNames']=fieldNames
#    else:
#        msg.append('Query Failed')
#        msg.append(repr(q))
#        msg.append('ID=2 for dbname='+str(dbname))
#        errorHandler(req,msg,1)


    if fieldInfo['idField']:
        try:
            idLoc=fieldInfo['fieldNames'].index(fieldInfo['idField'])
            fieldInfo['idLoc']=idLoc
        except:
            pass

    fieldInfo['idField']=fieldInfo['idField']
    fieldInfo['fieldTypes']=fieldTypes
    fieldInfo['fieldDefaults']=fieldDefaults

    # return:
    # fieldInfo['fieldNames'] - a list of the field names for tableName
    # fieldInfo['idField'] -  the PRI id field in tableName
    # fieldInfo['fieldTypes'] - dictionary, fieldTypes keyed by field names.
    # fieldInfo['fieldDefaults'] - dictionary, fieldDefaults keyed by field names.
    # fieldInfo['idLoc'] - the list index of the pri field?

    return fieldInfo

# ****************************************************************************
# ***************** dougs quote handler 10-23-02 *****************************

def quoteHandler(tmp):
    if tmp:
        # replace all occurances of ascii quotes in a string
        # with the upper ascii right and left quote characters
        # so that they won't affect the insert/update query
        theLetters = list(string.letters) + list(string.digits)+list('})]*!.,;')
        theString = list(tmp)
        sind = 0
        quotecount = 0
        for i in theString:
            if i == '"':
                quotecount = quotecount + 1
                # if there is a 'Letter' or a left hand quote in
                # front of the quote it's a right hand quote
                if sind > 0 and (string.count(theLetters, theString[sind-1]) >0 or theString[sind-1]=='\xe2\x80\x9c'):
    ##                       or theString[sind-1]=='&ldquo;'):
    ##                            theString[sind]='&rdquo;'
                    theString[sind]='\xe2\x80\x9d'
                # if there's not a 'Letter' in front of the quote
                # or if it's the first character then it's a left quote.
                else:
    ##                            theString[sind]='&ldquo;'
                    theString[sind]='\xe2\x80\x9c'
    
            sind = sind +1
    
        tmp=string.join(theString,"")

    return tmp

def convertImg(config,colvalue,file2Convert):
    
    error=''
    convertCommand=''
    commandSplit=config['convert2'].split(" ")
    convertedFile=commandSplit[-1]
    workingDir=os.getcwd()
    os.chdir(config['mediaPath'])
    
    # convert a file of one type to another type
    # the command is stored in config['convert2']
    try:

        inFile=open(file2Convert,"wb")
        inFile.write(colvalue)
        inFile.close()

        convertCommand=config['convert2'].replace("%S",file2Convert)
        
        os.system(convertCommand)
        
        outFile=open(convertedFile,"rb")
        colvalue=outFile.read()
        outFile.close()
#        x=2/0
    except:
        error="Could not convert "+file2Convert.upper() +", command failed:\\n\\n"+convertCommand+\
        "\\n\\n Conversions that result in multiple files will fail by default."\
        "\\n Spaces are not allowed in file names."\
        "\\n command syntax: command parameters %S outputfile"\
        "\\n %S will be replaced by the input filename."
    
    os.chdir(workingDir)
        

    return(colvalue,error)

def cleanTmp(config):

    # delete the tmp files 
    subDirs=os.listdir(config['mediaPath'])
    for thisItem in subDirs:
        if thisItem[0]!=".":
            if os.path.isdir(config['mediaPath']+thisItem):
                shutil.rmtree(config['mediaPath']+thisItem)
            elif os.path.isfile(config['mediaPath']+thisItem):
                os.remove(config['mediaPath']+thisItem)
    return

