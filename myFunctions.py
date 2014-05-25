import string
import db
import os
import os.path
import shutil
import kooky2
import MySQLdb

from mod_python import util #@UnresolvedImport

# use this call to check variable values
# util.redirect(req,"../testValue.py/testvalue?test="+repr(qresult))

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
    elif action in ('16','17'):
        parameter='?medit='+req.form['media']
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
        dbconnection.close()
    except:
        pass


        #~ util.redirect(req,"../testValue.py/testvalue?test="+repr(error))

    # if it's a good login then save it to the kooky table
    if loginAccepted:
        data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])

        data['username']=username
        data['userpass']=userpass

        kookied=kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])

    if cancelClicked:
        parameter='?action='+req.form['action']
    else:
        if loginAccepted:
            if action=='15':
                parameter='?media='+req.form['media']
            elif action in ('16','17'):
                parameter='?medit='+req.form['media']
            else:
#                parameter='?media='+req.form['media']
                parameter='?action='+req.form['action']
        else:
            parameter='?action=98'

    util.redirect(req,"../index.py"+parameter)

def getConfig(req,dbname):
    aqresult=''
    config={}
    config['configError']=''

    try:
        if dbname:
            fileName='config-'+dbname+'.txt'
        else:
            fileName='config.txt'

        apacheConfig=req.get_config()
        rootPath=apacheConfig['PythonPath'][11:-2]
        configFile=rootPath+"/"+'conf'+'/'+fileName
        config['rootPath']=rootPath
        config['configFile']=configFile

        try:
            confFile=open(configFile,"rb")
        except:
            # the given file failed so fall back to the default config file
            confFile=open(rootPath+"/"+"conf"+"/config.txt","rb")

        lines=confFile.readlines()
        confFile.close()

        primaries=[]
        # the values from the current conf file
        for thisLine in range(0,len(lines)):
            if "#" not in lines[thisLine] and '=' in lines[thisLine]:
                configData=lines[thisLine].split("=")
                config[configData[0].strip()]=configData[1].strip()

        # query mysql for it's values for the catTable
        try:
            q="show columns from "+config['catTable']
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisCol in qresult:
                if 'PRI' in thisCol[3]:
                    config['catIDfield']=thisCol[0]
                    primaries.append(thisCol[0])
                elif 'text' in thisCol[1]:
                    config['catNoteField']=thisCol[0]
    
            # just a quick check to see if the mysql info is correct
            # this will fail everytime, why did I put it here???
#             for thisCol in qresult:
#                 if config['catField'] in thisCol[0]:
#                     config['configError']='Query failed: '+q
        except:
            config['configError']='Query failed: '+q
            

        # query mysql for it's values for the itemTable
        try:
            q="show columns from "+config['itemTable']
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisCol in qresult:
                if 'PRI' in thisCol[3]:
                    config['itemIDfield']=thisCol[0]
                    primaries.append(thisCol[0])
                elif 'blob' in thisCol[1]:
                    config['itemIMGfield']=thisCol[0]
        except:
            config['configError']='Query failed: '+q

        # query mysql for it's values for the mediaTable
        try:
            q="show columns from "+config['mediaTable']
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
            for thisCol in qresult:
                if 'PRI' in thisCol[3]:
                    config['mediaIDfield']=thisCol[0]
                    primaries.append(thisCol[0])
        except:
            config['configError']='Query failed: '+q

        config['primaries']=primaries
        config['catImagePath']=rootPath+"/catimages/"
        config['itemImagePath']=rootPath+"/itemimages/"
        config['mediaPath']=rootPath+"/tmp/"
        config['itemUniqueID']=config['itemUniqueID'].split()
        config['allItems']=config['allItems'].split(" ")
        config['catSearchFields']=config['catSearchFields'].split()
        # windows users will need to provide a fixed path to convert.exe
#         config['convertExe']=rootPath+"/convert/convert.exe"
        config['convertExe']='convert'
        config['owner']='owner'

        # config defaults
        if not config['displaylogo']:
            config['displaylogo']='displaylogo.png'
        if not config['popupbackground']:
            config['popupbackground']=config['displaylogo']
            
#         util.redirect(req,"testValue.py/testvalue?test="+repr(config['configError']))

    except:
        config['configError']="configError"

    return config

def writeConfig(req):

    action=''

    try:                # SAVE clicked?
        action=req.form['savebutton.x']
    except:
        try:
            action=req.form['updatebutton.x']
        except:
            action=''
    if action:
        # This just writes a config file, however some config variables are not present in the file.
        # Some are gotten by inference or from the mysql db.
        # Because the dbname is passed as a hidden value and as a form data
        # I get a list of two dbname values. This is unique to this function
        # So I'm going to leave it this way as it makes the rest of this program more readable.
        dbname=(req.form['dbname'][0].value).strip()
        config=getConfig(req,dbname)

        fileHeader=[\
        '# configuration file for all 3 table dbs (3t)',\
        '# Use this form to edit the configuration, editing this file by hand requires strict adherence to specific formatting.',\
        '#',\
        '# This file (config-(dbname).txt) must exists and must be located in the conf subdirectory of the program directory.',\
        '# This form will create the file if it is found to be missing or is a new configuration.',\
        '# To complete a new configuration you will need catImages in place under the dir "catImages/(dbname)"',\
        '# The dir is automatically created and a default img is provided.',\
        '#',\
        '# In order to use the convert2jpg feature you will need to install the Imagemagick convert utility and any',\
        '# required support files in the 3t/convert directory. This location is hardcoded because I found that at least',\
        '# some windows installations already have a convert.exe file (filesystem conversion). Ghostscript will also need to',\
        '# be installed on your system.',\
        '#',\
        '#',\
        '# start of configuration'\
        ]

        fileBody=[\
            '## Enter a name to print on top of the logo image (no default).',\
            'displayname='+req.form['displayname'].strip(),\
            '',\
            '## Enter a location for the displayname (top,middle,bottom).',\
            'displaynamelocation='+req.form['displaynamelocation'].strip(),\
            '',\
            '## Enter the name of the image to use as your logo (a default is provided).',\
            'displaylogo='+req.form['displaylogo'].strip(),\
            '',\
            '## Enter the name of the image to use as the popup background (default=displaylogo).',\
            'popupbackground='+req.form['popupbackground'].strip(),\
            '',\
            '## Enter the email contact address (no default is provided).',\
            'emailcontact='+req.form['emailcontact'].strip(),\
            '',\
            '## Enter the database name for the mysql server (no default).',\
            'dbname='+dbname,\
            '',\
            '## Enter the hostname for the mysql server (default is localhost).',\
            'selectedHost='+req.form['selectedHost'].strip(),\
            '',\
            '## Enter the name of the category table (no default).',\
            'catTable='+req.form['catTable'].strip(),\
            '',\
            '## Enter the name of the item table (no default).',\
            'itemTable='+req.form['itemTable'].strip(),\
            '',\
            '## Enter the name of the media table (no default).',\
            'mediaTable='+req.form['mediaTable'].strip(),\
            '',\
            '## Enter the catTable catagory field (enumeration field).',\
            'catField='+req.form['catField'].strip(),\
            '',\
            '## Enter the catTable informational field (no default).',\
            '## Used to visually provide a relatationship for media info.',\
            'catInfo='+req.form['catInfo'].strip(),\
            '',\
            '## Enter the category table column that results will be sorted by (default ?).',\
            'orderbyField='+req.form['orderbyField'].strip(),\
            '',\
            '## Enter a space seperated list of item table column names',\
            '## that will uniquely identify an item (no default).',\
            'itemUniqueID='+req.form['itemUniqueID'].strip(),\
            '',\
            '## Enter a space seperated list of item table column names',\
            '## that will comprise the All_Items table (no default).',\
            'allItems='+req.form['allItems'].strip(),\
            '',\
            '## Enter a space seperated list of category table column names',\
            '## that you want included in boolean search results (no default).',\
            'catSearchFields='+req.form['catSearchFields'].strip(),\
            '',\
            '## On startup display the last record entered (no default).',\
            '## Any value will enable, leave blank to disable.',\
            'lastupdate='+req.form['lastupdate'].strip(),\
            '',\
            '## Convert PDF, Postscript and TIFF files to JPG, details above.',\
            '## Any value will enable, leave blank to disable.',\
            'convert2jpg='+req.form['convert2jpg'].strip(),\
            '',\
            ]

        fileFooter=[\
            '',\
            '',\
            '# end of configuration file'\
            ]

        # write the lines to disk
        baseDir=config['configFile'].split("/")
        fileName="/".join(baseDir[:-1])+"/config-"+dbname+".txt"

        cfgFile=open(fileName,"wb")

        for thisLine in fileHeader:
            cfgFile.write(thisLine+'\n')
        for thisLine in fileBody:
            cfgFile.write(thisLine+'\n')
        for thisLine in fileFooter:
            cfgFile.write(thisLine+'\n')

        cfgFile.close()

        # create the catImages dbname dir if not found
        # but you will still need to populate it with images
        # allthough the default image is copied over.
        catImagesDir=config['rootPath']+"/catimages/"
        catDBdir=catImagesDir+dbname+"/"
        if os.path.isdir(catDBdir):
            try:
                os.chmod(catDBdir,0777)
            except:
                pass
        else:
            try:
                os.mkdir(catDBdir)
                os.chmod(catDBdir,0777)
            except:
                pass
        # create the dbImages dbname dir if not found
        # but you will still need to populate it with images
        # allthough the default image is copied over.
        dbImagesDir=config['rootPath']+"/images/"+dbname+"/"
        if os.path.isdir(dbImagesDir):
            try:
                os.chmod(dbImagesDir,0777)
            except:
                pass
        else:
            try:
                os.mkdir(dbImagesDir)
                os.chmod(dbImagesDir,0777)
            except:
                pass

        # copy the default cat image file over if needed
        # it should be the only file in the catImagesDir
        dirList=os.listdir(catImagesDir)
        for thisEl in dirList:
            if os.path.isfile(catImagesDir+thisEl):
                try:
                    shutil.copy(catImagesDir+thisEl,catDBdir)
                except:
                    pass

        # copy the default logo image file to images/dbname
        defaultLogoFile=config['rootPath']+'/images/defaultlogo.png'
        dbImageDir=config['rootPath']+'/images/'+dbname
#        util.redirect(req,"../testValue.py/testvalue?test="+repr(defaultLogoFile)+" "+repr(logoImageDir))
        try:
            shutil.copy(defaultLogoFile,dbImageDir)
        except:
            pass


    else:
        # cancel button was clicked
        pass

    # return to program
    util.redirect(req,"../index.py")

def checkConfig(config):




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
        cols[config['catField']]=req.form['system'].value
    except:
        try:            # UPDATE clicked
            action=req.form['updatebutton.x']
            action='update'
            cols[config['catIDfield']]=req.form['catID'].value
        except:
            action='cancel'

#    util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form.list))
    if action !='cancel':

        what=doSql(req,action,cols,config['catIDfield'],config['dbname'],config['catTable'],config['selectedHost'],config['owner'])

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

#        util.redirect(req,"../testValue.py/testvalue?test="+repr(what))
        if what[0]:
            parameter="?error="+what[0]
        elif action=='insert':
            insertID=what[1]
            parameter="?action=4&item="+str(insertID)
        else:
            parameter="?action=3"
    else:
        parameter="?action=3"

    util.redirect(req,"../index.py"+parameter)

def media(req):

    config=getConfig(req,req.form['dbname'].value)

    # get the column names and column types for tableName
    cols={}
    fieldInfo=getFieldInfo3(req,config['selectedHost'],config['dbname'],config['mediaTable'])
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
        #  what table and record to relate to
        cols[config['catIDfield']]=req.form['catID'].value
    except:
        try:            # UPDATE clicked
            action=req.form['updatebutton.x']
            action='update'
            cols[config['mediaIDfield']]=req.form['mediaID'].value
        except:
            action='cancel'

#    util.redirect(req,"../testValue.py/testvalue?test="+repr(req.form.list))

    #  set the realted table, so this returns to the correct data
    tableID=req.form['catID']

    if action!='cancel':

        what=doSql(req,action,cols,config['mediaIDfield'],config['dbname'],config['mediaTable'],config['selectedHost'],config['owner'])

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

    # get the column names and column types for tableName
    cols={}
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
        if what[0]:
            parameter="?error="+what[0]
        else:
#            insertID=what[1]
            parameter="?media="+str(tableID)
    else:
        parameter="?action=3"

    util.redirect(req,"../index.py"+parameter)

def delMedia(req):
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
            parameter="?action=3&item="+str(itemID)
    else:
#        parameter="?media="+mediaRecord
        parameter="?action=3&item="+str(itemID)

    util.redirect(req,"/3t/index.py"+parameter)

def delCat(req):
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
            parameter="?action=8&category="+str(currentCat)
    else:
#        parameter="?action=8"
        parameter="?action=8&category="+str(currentCat)

    util.redirect(req,"/3t/index.py"+parameter)

def delItem(req):
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

def doSql(req,action,cols,idField,dbname,tableName,selectedHost,owner):
    # this handles all insert, update, and delete sql
    # So, if the user is not logged in or doesn't have permission then this will fail
    # the default user (dbname) should only have select permission
    
    error=""
    insertID=''
    config=getConfig(req,req.form['dbname'].value)

    data=kooky2.myCookies(req,'get','',dbname,selectedHost)
    #~ util.redirect(req,"../testValue.py/testvalue?test="+repr(data))

    try:
        username=data['username']
        userpass=data['userpass']
    except:
        username=dbname
        userpass=dbname

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
                    if config['convert2jpg']:
                        conversion=convertImg(config,colvalue)
                        colvalue=conversion[0]
                        error=conversion[1]
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

#        util.redirect(req,"../testValue.py/testvalue?test="+str(q)+repr(setValues))

        try:
            dbconnection = MySQLdb.connect(host=selectedHost,user=username,passwd=userpass,db=dbname)
            xcursor = dbconnection.cursor()

            xcursor.execute(q,(setValues))
            xcursor.execute("SELECT LAST_INSERT_ID()")
            insertID=xcursor.fetchone()[0]
        except:
#            qstr=q.replace('%s','value')
            error='Insert error for '+tableName  +" and user "+str(username)+".\\n\\n Perhaps you are not the owner of this record or are not logged in"
            #~ error=" q="+str(setValues)
        try:
            xcursor.close()
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
                    if config['convert2jpg']:
                        conversion=convertImg(config,colvalue)
                        colvalue=conversion[0]
                        error=conversion[1]
                else:
                    colvalue="skipme"

            # if it's a set field then change that colvalue
            elif 'set(' in fieldTypes[colname.lower()]:
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
            if colvalue=='skipme':
                pass
            else:
                setCols=setCols+",`"+colname+'`=%s'
                setValues.append(colvalue)

        setCols=setCols[1:]
        setValues=tuple(setValues)

        # if there is an owner field defined, get the owner and check it against current username
        if owner in fieldNames:
            q='select '+owner+' from '+tableName+" where `"+idField+"`='"+str(idValue)+"'"
                        
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
#        util.redirect(req,"../testValue.py/testvalue?test="+repr(q))

        try:
            dbconnection = MySQLdb.connect(host=selectedHost,user=username,passwd=userpass,db=dbname)
            cursor = dbconnection.cursor()
            cursor.execute(q,setValues)
        except:
            error="Update error for "+tableName +" and user "+str(username)+".\\n\\n Perhaps you are not the owner of this record or are not logged in"

        try:
            xcursor.close()
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
            error="Delete error for "+tableName  +" and user "+str(username)+".\\n\\n Perhaps you are not the owner of this record or are not logged in"

        try:
            xcursor.close()
        except:
            pass
        try:
            dbconnection.close()
        except:
            pass
        ########################

    return (error,insertID)

def getServerInfo(selectedHost, variableName):

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
            # for matching purposes ?
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

def convertImg(config,colvalue):
    
    # convert tiff pdf and postscript files
    # this will catch most files, not all
    error=""
    fileType=""
    fileTypes={"MM":"tif","II":"tif","%PDF":"pdf","%!PS":"ps"}
    fileSample=colvalue[0:16]
    fileMagic=fileTypes.keys()
    for thisType in fileMagic:
        if thisType in fileSample:
            fileType=fileTypes[thisType]

    # convert a file to jpg
    # requires gostscript to be installed and in exe path                            
    # requires imagemagick convert to be installed. Location to convert exe
    # is hard coded in config because some windows systems have other "convert" executables
    try:
        imagename=config['mediaPath']+'/convert'
        convertFile=imagename+"."+fileType
        jpgFile=imagename+".jpg"
        convertExe=config['convertExe']
        imgFile=open(convertFile,"wb")
        imgFile.write(colvalue)
        imgFile.close()
        convertCommand=convertExe+" "+convertFile+" "+jpgFile
        os.system(convertCommand)
        imgFile=open(jpgFile,"rb")
        colvalue=imgFile.read()
        imgFile.close()
#        x=2/0
    except:
        colvalue=""
        error="Could not convert "+fileType.upper() +" to JPG!\\nAre ghostscript and IM convert installed? The location of IM convert is hardcoded in getConfig.\\nOnly single page PDF docs are allowed."
        
        
    return(colvalue,error)   