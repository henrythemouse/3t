import db
import string
import strict401gen
import os
import datetime
import imghdr
import kooky2
import myFunctions
import shutil
from operator import itemgetter




'''
$LastChangedDate: 2014-07-07 13:16:39 -0700 (Mon, 07 Jul 2014) $
$Rev: 4 $
'''

from mod_python import psp,util #@UnresolvedImport

'''
$LastChangedDate: 2014-07-07 13:16:39 -0700 (Mon, 07 Jul 2014) $
$LastChangedRevision:$
'''
'''
BUG FIXES THAT NEED TO PROPIGATE TO 2TABLE

'''
'''
TO DO

For Item title ("Details for .....") how do I determine the order of the fields?
    In the Read db the author's name lastname firstname, should be reversed.
    I use the itemUniqueID config value.

Do I want to insert the username at the start of the note? Provide a conf option?
    The option is ... if one includes a 'owner' field in a table then the script will
    insert the owner name in front of the first field of the mediaTable. No owner
    field means no owner inserted. Simple?

catID is blank in mediaCreate, so the caption can't contain the record reference.
        I re-enabled catID in kooky get to fix this, but I don't recall needing to do that b4
        and I wonder what affect it will have elsewhere.

All/All results are too wide in iceweasel on my hp. Due to too many large columns.
    I needed to reset the max col len down to 18 (from 25). I may need to include this in
    the config as a setting? Also needed to lower font size to 8 (from 10). This doesn't
    seem very dependable.

Added an owner field to the table definition for applicable dbs, so that only the owner of a entry can edit
    the entry.  This is essentially a row privilege (which mysql doesn't supply). It's in addition to
    any login privileges enabled. You can have mysql update privileges for a table, but if you aren't the
    owner of a particular record then you still won't be able to edit it.

Login: In addition one must login to create an entry, logout is optional. The kooky table will remember
    the login if you don't logout, so next time you load the page you'll already be logged in. There is a
    default user that is enabled when no one is logged in, this user only  has select privileges. For a user
    to have write privileges the db has to have that user setup and insert/update privileges enabled.


Save a new author and it doesn't display that author on return.

Field widths in mediatable are not constant (in read the rating will have a large width at times). Need headerWidths for media table.

Need 'no cookie' warning.

New feature: auto load the last modified media record apon first access?
Or add a link to it via the toolbar?

'''


# I USE THE WORD 'BROKEN' TO MARK BROKEN CODE
# I USE '!!' TO MARK AREAS THAT NEED ATTENTION
# The more '!!' in a row the more serious the need.
# I use the '?' to indicate I'm unsure about what I want.
# use this call to check variable values
# util.redirect(req,"testValue.py/testvalue?test="+repr(qresult))

# ************************** VERSION 2.0 dev *****************************
# set some variables SPECIFIC to installation

# *********************************************************************

# this is a global variable, I don't think I need to pass this with functions !! but I do.

#=================================================================================
#=================================================================================

def index(req,currentCat=0,currentItem=1,action=0):


    action=int(action)
    caption=''
    resultTable=''
    headerWidths=''
    v={}
    itemImage=''
    cancelAction=0
    username=''
    userpass=''
    searchMode=''
    dbname=''
    supportTableName=''
    itemReq=''
    catReq=''

    try:
        x=req.form.list
#         util.redirect(req,"testValue.py/testvalue?test="+repr(x))
    except:
        pass

    # if the url has a config name passed I use it to get config data from _config table
    # if no config name is passed then I have to use the value stored in the browser cookie
    # this is why the browser cookie must have a generic name not dependent on the dbname
    # which is why only one db can be accessed per browser at a time
    try:
        dbname=req.form['config'].value
        config=myFunctions.getConfig(req,dbname)
#         kookyDB=kooky2.myCookies(req,"","",dbname,"")
        
    except:
        # all I want here is the dbname from the browser cookie
        # which gives me the config name to retrieve the configuration
        #
        kookyDB=kooky2.myCookies(req,"db","","","")
        try:
            config=myFunctions.getConfig(req,kookyDB)
        except:
            config=myFunctions.getConfig(req,"")


#         util.redirect(req,"testValue.py/testvalue?test="+repr(kookyDB))
    
    # check for a config error
    if config['configError']=="configError":
        action=100
#         action=20

#        util.redirect(req,"?error="+config['configError'])
#    elif config['configError']:
#        # just for debugging where the error occurred
#        pass
#        util.redirect(req,"testValue.py/testvalue?test="+repr(config['configError']))
    else:
        # write item images to disk for now until I can use them from the db
        writeImgs(config)
        # just get the cookieID
        cookieID=kooky2.myCookies(req,"","","","")

        try:
            # try to make the tmp/+cookieID path for storing media in the case it doesn't exist
            os.mkdir(config['mediaPath']+cookieID)
        except:
            pass

        try:                # if available, get the category formdata
            error=req.form['error']
            #~ if error=="item":
                #~ error="An ERROR occurred while saving the data."+\
                #~ "You may have tried to save an image that was too big."+\
                #~ "Images must be less than 65KB in size. Try again."
            #~ elif error=="cat":
                #~ error="An ERROR occurred while saving the data."+\
                #~ "You may have enter the date incorrectly."+\
                #~ "The accepted date formats are YYYY-MM-DD, YYYY/MM/DD "+\
                #~ "or YYYYMMDD. Try again."
        except:
            error=''

#        util.redirect(req,"testValue.py/testvalue?test="+repr(config))

        try:                # if available, get the category formdata
            catSelected=req.form['category']
        except:
            catSelected=''

        try:                # if available, get the item formdata
            itemSelected=req.form['item'].value
            action=4
        except:
            itemSelected=''

        try:                # if available, get the item formdata
            searchText=req.form['searchText']
        except:
            searchText=''

        try:                # if available, get the cat record formdata - edit a record
            catID=req.form['edit']
            catReq=catID
            action=12
        except:
            try:                # if available, get the cat record formdata - edit a record
                catID=req.form['alledit']
                catReq=catID
                action=12
            except:
                catID=''

        try:                # if available, get the cat record formdata - media display
            media=req.form['media']
            mediaID=media
            action=15
            if 'Inew' in media:
                itemReq=media[4:]
                action=17
            elif 'I' in media:
                itemReq=media[1:]
                action=15
            elif 'new' in media:
                catID=media[3:]
                mediaID=media[0:3]
                action=17
        except:
            try:                # edit the media record
                mediaID=req.form['medit']
                action=16
            except:
                mediaID=''
#         util.redirect(req,"testValue.py/testvalue?test="+repr(action)+"***"+str(mediaID)+'***'+str(req.form))
        try:
            supportTableName=req.form['supportTableName']
            if supportTableName=="Support Tables":
                supportTableName=''
                action=20
#             else:
#                 action=23
        except:
            pass
        
        try:
            supportTableName=req.form['supportedit']
            supportID=req.form['supportID']
            action=24
        except:
            supportID=0
        
        try:
            supportTableName=req.form['supportcreate']
            action=25
        except:
            pass
        
            
        try:
            popup=req.form['popup'].value
        except:
            popup=''
            
#         util.redirect(req,"testValue.py/testvalue?test="+repr(config['dbname'])+"***"+str(dbname))

        #~ if action:          # load saved data
        # if I set this back to 'if action' then the login is reset on startup
        # if I do this then the login can be recovered and used again and again
        try:
            data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])
            results=data['results']
            currentCat=data['currentCat']
            currentItem=data['currentItem']
            itemImage=data['itemImage']
            item=data['item']
            catImages=data['catImages']
            cancelAction=data['cancelAction']
            username=data['username']
            userpass=data['userpass']
#             supportTableName=data['supportTableName']
            if not username:
                username=dbname
                config['login']=''
            else:
                config['login']='stored'
            if not userpass:
                userpass=dbname
                config['login']=''
            else:
                config['login']='stored'
            try:
                # is search button clicked?
                searchButton=req.form['searchButton.x'].value
                try:
                    # get searchMode if sent
                    searchMode=req.form['searchMode'].value
                except:
                    searchMode=""
            except:
                # use saved data
                searchMode=data['searchMode']
                searchText=data['searchText']

            if not catID:
                catID=data['catID']
        except:
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(data))
            pass

#     util.redirect(req,"testValue.py/testvalue?test="+str(searchButton))    
    
#    itemSelected=1
    # *******************************************
    # item image and navagation
    if action in (1,2,3,4):       # index item

        # need to refresh item in case of a newly inserted item
        item=itemData(currentItem,config)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        currentItem=indexItem(item,itemSelected,action)
        item=itemData(currentItem,config)
        itemSelect=itemForm(item[4],currentItem)
        itemImage=itemImg(itemImage,item,config)
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        results=itemQuery(currentItem,item,config)
        cleanTmp(config)

        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        cancelAction=3
#        colSums=catSum(currentItem,config)
#        util.redirect(req,"testValue.py/testvalue?test="+repr(colSums))
        if currentItem==0:
            # this is for ALL items listing
            headerWidths=getItemColWidths(resultHeader,config)
            resultTable=itemAllTable(resultData,"",resultHeader,headerWidths,config)
        else:
            # a single item listing
            resultTable=itemTable(str(item[1]),resultData,config)

    # *******************************************
    # category image and navagation

    elif action in (5,6,7,8):     # category

        itemSelect=itemForm(item[4],currentItem)
        currentCat=indexCat(currentCat,catImages,catSelected,action)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        results=catQuery(req,catImages[currentCat][0],item[1],config)
        cleanTmp(config)

        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        cancelAction=7
#         util.redirect(req,"testValue.py/testvalue?test="+repr(results))

        headerWidths=getCatColWidths(resultHeader,config)
        resultTable=catTable(resultData,catImages[currentCat][0],resultHeader,headerWidths,config)
#         util.redirect(req,"testValue.py/testvalue?test="+str(resultTable))

    elif action==10:     # edit item
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        # not that in all insert/update forms I use 'result' and not 'results'
        # this way the binary data is not save to the cookie table
        result=editItem(currentCat,item,config)

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==11:     # create item
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        result=createItem(currentCat,item,config)

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==12:     # edit catagory
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
#         util.redirect(req,"testValue.py/testvalue?test="+str(catImages[currentCat][0]))
        result=editCat(catImages[currentCat][0],catID,config)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(result))

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==13:     # create catagory
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        result=createCat(catImages[currentCat][0],catID,config)

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==14:     # search requested
       
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
#         util.redirect(req,"testValue.py/testvalue?test="+str(searchText)+str(searchMode))
        results=searchQuery(searchText,searchMode,catImages[currentCat][0],item[1],config)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(results[-3]))

        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        cancelAction=14

        headerWidths=getCatColWidths(resultHeader,config)
        resultTable=catTable(resultData,catImages[currentCat][0],resultHeader,headerWidths,config)

    elif action==15:         # show note/media
        try:
            if mediaID[0]!="I":
                catID=mediaID
        except:
            pass
        if itemReq:
            for y in range (0,len(item[4])):
                if item[4][y][1]==itemReq:
                    currentItem=y
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        item=itemData(currentItem,config)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        results=mediaQuery(mediaID,config)

        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]

        headerWidths=getMediaColWidths(req,config)
#         resultTable=mediaTable(resultData,cookieID['kookyID'],mediaID,config)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(resultData))
        result=mediaTable(resultData,cookieID,mediaID,config)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(result[1]))
        resultTable=result[0]
        
    elif action==16:     # edit media
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        result=editMedia(mediaID,catID,item,config)
#        util.redirect(req,"testValue.py/testvalue?test="+repr(result[-1]))

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]
        catID=result[4]

    elif action==17:     # create media
        if itemReq:
            for y in range (0,len(item[4])):
                if item[4][y][1]==itemReq:
                    currentItem=y
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        item=itemData(currentItem,config)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(item))
        result=createMedia(mediaID,catID,item,config)

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]
        #~ catID=result[4]

    elif action==20:     # about

        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        results=aboutInfo(config)
        
        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]

        resultTable=aboutTable(resultData,config)

    elif action==21:     #edit config

        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        result=editConfig(req,config)
            
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==22:     #create config
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        result=createConfig(req,config)

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==23:     #show support table
        
#         currentItem=indexItem(item,itemSelected,action)
#         itemImage=itemImg(itemImage,item,config)
#         catImages=catImgs(config)
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#         catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
        
#         util.redirect(req,"testValue.py/testvalue?test="+repr(catImages)+" "+str(supportTableName))
        result=supportTable(supportTableName,config)
        # in case the _category table has been edited this will refress the images
        catImages=catImgs2(config)
        
#         util.redirect(req,"testValue.py/testvalue?test="+repr(catImages)+" "+str(supportTableName))

        # parse the results list
        caption='supportTableHeader'
        resultTable=result[0]
        headerWidths=result[1]
        resultHeader=result[2]

    elif action==24:     #edit support record
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(req.form.list)+" "+str(supportID))

        result=editSupport(supportTableName,supportID,config)

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==25:     #create support record
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
#        catImage=catImages[currentCat][1]
        supportSelect=supportForm(supportTableName,config)
        search=searchForm(searchText,searchMode)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(supportTableName))

        result=createSupport(supportTableName,config)
#         util.redirect(req,"testValue.py/testvalue?test="+repr(result))

        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]


#     elif action==100:     # configure dialog
#         # the emergency configuration dialog
#         # when something is wrong in the config.txt file
#         # the actual branch is done below
# #         result=supportTable("_config",config)
#         result=createSupport("_config",config)
# #         util.redirect(req,"testValue.py/testvalue?test="+repr(req.form.list)+" "+str(result))
# 
#         # parse the results list
#         supportTableName="_config"
#         caption='supportTableHeader'
#         resultTable=result[0]
#         headerWidths=result[1]
#         resultHeader=result[2]
#         action=0
#         pass

    elif action<100:               # no action - use defaults
        if popup:
            # this goes back to the item display
            # I could do more and return to ???, not a safe bet however.
            item=itemData(currentItem,config)
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(currentItem))
            currentItem=indexItem(item,itemSelected,action)
            itemSelect=itemForm(item[4],currentItem)
            itemImage=itemImg(itemImage,item,config)
#             catImages=catImgs(config)
            catSelect=catForm(catImages,currentCat)
#            catImage=catImages[currentCat][1]
            supportSelect=supportForm(supportTableName,config)
            search=searchForm(searchText,searchMode)
            results=itemQuery(currentItem,item,config)
            cleanTmp(config)

            # parse the results list
            caption=results[0]
            resultHeader=results[1]
            resultData=results[2]

            resultTable=itemTable(str(item[1]),resultData,config)
            
        elif config['lastupdate']=='YES':

#            util.redirect(req,"testValue.py/testvalue?test="+repr(config))
            itemID,mediaID=lastUpdate(config)
            item=itemData2(itemID,config)
            currentItem=indexItem(item,itemSelected,action)
            itemSelect=itemForm(item[4],currentItem)
            itemImage=itemImg(itemImage,item,config)
            catImages=catImgs2(config)
#             util.redirect(req,"testValue.py/testvalue?test="+str(catImages)+"----"+str(currentItem))
            currentCat=0
            catSelect=catForm(catImages,currentCat)
#            catImage=catImages[currentCat][1]
            supportSelect=supportForm(supportTableName,config)
            search=searchForm(searchText,searchMode)
            results=mediaQuery(mediaID,config)

#             util.redirect(req,"testValue.py/testvalue?test="+repr(results)+"----"+str(item[1]))
            # parse the results list
            #~ cookieIDtext=kooky2.myCookies(req,'','','','')#['kookyID']

            caption="Most Recent Entry: "+results[0]
            resultHeader=results[1]
            resultData=results[2]

            headerWidths=getMediaColWidths(req,config)
            #~ data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])
            #~ username=data['username']
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(data))
            result=mediaTable(resultData,cookieID,mediaID,config)
            resultTable=result[0]
            
        else:

#             item=itemData2(1,config)
            item=itemData(currentItem,config)
#             util.redirect(req,"testValue.py/testvalue?test="+repr(currentItem)+"----"+str(item))
            currentItem=indexItem(item,itemSelected,action)
            itemSelect=itemForm(item[4],currentItem)
            itemImage=itemImg(itemImage,item,config)
            catImages=catImgs2(config)
#             util.redirect(req,"testValue.py/testvalue?test="+repr(catImages)+"----"+str(item[4]))
            catSelect=catForm(catImages,currentCat)
#            catImage=catImages[currentCat][1]
            supportSelect=supportForm(supportTableName,config)
            search=searchForm(searchText,searchMode)
            results=itemQuery(currentItem,item,config)
            cleanTmp(config)
#             util.redirect(req,"testValue.py/testvalue?test="+repr(results)+"----"+str(item[1]))

            # parse the results list
            caption=results[0]
            resultHeader=results[1]
            resultData=results[2]

            resultTable=itemTable(str(item[1]),resultData,config)

    if action<100:
        # actions =>100 are errors
        # either a item or a catagory
        try:
            activeForm=result[3]
        except:
            activeForm=''

        data={\
            'item':item,\
            'currentCat':currentCat,\
            'currentItem':currentItem,\
            'itemImage':itemImage,\
            'catImages':catImages,\
            'searchText':searchText,\
            'searchMode':searchMode,\
            'catID':catID,\
            'cancelAction':cancelAction,\
            'username':username,\
            'userpass':userpass,\
            'results':results\
            }

#        util.redirect(req,"testValue.py/testvalue?test="+"kooky "+repr((searchMode)))
        kookied=kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])

        # set the template name
        mainForm='templates/main4.html'
        # check for an item relate cat record to enable/disable delete function
        relatedCat=relatedRecords(item[1],config)
#        relatedCat=relatedRecords(currentItem,config)
#         util.redirect(req,"testValue.py/testvalue?test="+"kooky "+repr((kookied)+repr(currentItem)))

        # the dic of values to pass to the html page
        v['loginValue']=config['login']
        v['theme']=config['theme']
        v['itemSelected']=itemSelected
        v['action']=action
        v['popup']=popup
        v['relatedCat']=relatedCat
        v['dogleg']=username
        v['cancelAction']=str(cancelAction)
        v['error']=error
        v['dbname']=config['dbname']
        v['headerWidths']=headerWidths
        v['mediaTable']=config['mediaTable']
        v['catSelect']=catSelect
        v['itemSelect']=itemSelect
        v['supportSelect']=supportSelect
        v['supportTableName']=supportTableName
        v['catImages']=catImages
        v['itemImage']=itemImage
        v['caption']=caption
        v['resultHeader']=resultHeader
        v['resultTable']=resultTable
        v['activeForm']=activeForm
        v['mainTitle']=item[0]
        v['mediaID']=mediaID
        v['itemID']=item[1]
        v['catID']=catID
        v['supportID']=supportID
        v['currentItem']=str(currentItem)
        v['currentCat']=str(currentCat)
        v['search']=search
        v['displayname']=config['displayname']
        v['displaynamelocation']=config['displaynamelocation']
        v['displaylogo']=config['displaylogo']
        v['popupbackground']=config['popupbackground']
        v['emailcontact']=config['emailcontact']

    else:



#         util.redirect(req,"testValue.py/testvalue?test="+repr(config['configTable']))
        result=createSupport(config['configTable'],config)
        caption='supportTableHeader'
        resultTable=result[2]
#         headerWidths=result[1]
#         resultHeader=result[2]
#         util.redirect(req,"testValue.py/testvalue?test="+repr(v)+"------"+str(result))

        mainForm='templates/conf2.html'
        v['dbname']=config['dbname']
        v['dogleg']=username
        v['popup']=''
        v['caption']=caption
#         v['resultHeader']=resultHeader
        v['resultTable']=resultTable
#         v['supportSelect']=supportSelect
        v['supportTableName']="_config"
        v['emailcontact']=""
        v['config']=config
        
#         mainForm='templates/conf.html'
# 
#         v['message1']="THIS IS A DEFAULT CONFIGURATION DIALOG"
#         v['message2']="EITHER SOMETHING IS WRONG IN THE CONFIGURATION FILE"
#         v['message3']="A CRITICAL VALUE HAS CHANGED AND THE PROGRAM CAN'T START"
#         v['message4']="CHECK THE VALUES BELOW AND EDIT THEM AS NEEDED"
#         v['message5']="********************************************************"
#         if dbname:
#             v['configName']='-'+dbname
#         else:
#             v['configName']=''

#    util.redirect(req,"testValue.py/testvalue?test="+repr(v))

    # call the html doc passing it the data
    return psp.PSP(req,mainForm,vars=v)



# ===============================================================
#               support functions
#

############ search functions

def searchQuery(searchText1,searchMode,categoryName,itemID,config):

    selectFields,catHeader=catColumns(categoryName,itemID,config)
    itemFullTextCols,catFullTextCols,mediaFullTextCols=getFullTextCols(config)
    itemBooleanFields,catBooleanFields,mediaBooleanFields=getBooleanFields(config)

    # all searchMode does is add enum fields
    # change the mode to boolean and force phrase searching
    # phrase searching seems allow special character searching
    if searchMode:
        catFullTextCols=catFullTextCols+catBooleanFields
        itemFullTextCols=itemFullTextCols+itemBooleanFields
        mediaFullTextCols=mediaFullTextCols+mediaBooleanFields
        mode=' IN BOOLEAN MODE'
        searchText="'"+'"'+searchText1+'"'+"'"
    else:
        mode=""
        searchText="'"+searchText1+"'"


    if itemID=='0': #All_Items
        if categoryName[:3]=='All':
            if searchText:
                # the  search query that searches all the category records for all the items for searchtext
                # all_items, all_cats,  searchText
                q="select distinct "+selectFields+\
                " from `"+config['catTable']+\
                "` left join `"+config['itemTable']+"` on `"+\
                config['catTable']+"`.`"+config['itemIDfield']+"`=`"+config['itemTable']+"`.`"+config['itemIDfield']+\
                "` left join `"+config['mediaTable']+"` on `"+\
                config['mediaTable']+"`.`"+config['catIDfield']+"`=`"+config['catTable']+"`.`"+config['catIDfield']+\
                "` where "+ "(MATCH ("+catFullTextCols+") AGAINST ("+searchText+" "+mode+")"+\
                " or MATCH ("+itemFullTextCols+") AGAINST ("+searchText+" "+mode+")"+\
                " or MATCH ("+mediaFullTextCols+") AGAINST ("+searchText+" "+mode+"))"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

            else:
                # get all records for all items
                # all_items, all_cats, NO searchText
                q="select "+selectFields+" from `"+config['catTable']+\
                "` left join `"+config['itemTable']+"` on `"+\
                config['catTable']+"`.`"+config['itemIDfield']+\
                "`=`"+config['itemTable']+"`.`"+config['itemIDfield']+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

        else:
            if searchText:
                # all_items, selected_cat, searchText
                q="select distinct "+selectFields+\
                " from `"+config['catTable']+\
                "` left join `"+config['mediaTable']+"` on `"+\
                config['mediaTable']+"`.`"+config['catIDfield']+"`=`"+config['catTable']+"`.`"+config['catIDfield']+\
                "` left join `"+config['itemTable']+"` on `"+\
                config['catTable']+"`.`"+config['itemIDfield']+\
                "`=`"+config['itemTable']+"`.`"+config['itemIDfield']+\
                "` where `"+config['catColumn']+"`='"+categoryName+"'"+\
                " and (MATCH ("+catFullTextCols+") AGAINST ("+searchText+" "+mode+")"+\
                " or MATCH ("+itemFullTextCols+") AGAINST ("+searchText+" "+mode+")"+\
                " or MATCH ("+mediaFullTextCols+") AGAINST ("+searchText+" "+mode+"))"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

            else:
                # get records in this category all items
                # all_items, selected_cat, NO searchText
                q="select "+selectFields+" from `"+config['catTable']+\
                "` left join `"+config['itemTable']+"` on `"+\
                config['catTable']+"`.`"+config['itemIDfield']+\
                "`=`"+config['itemTable']+"`.`"+config['itemIDfield']+\
                "` where `"+config['catColumn']+"`='"+categoryName+"'"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"


    else: # selected_item
        if categoryName[:3]=='All':
            if searchText:
                # the  category search limited to the selected item and the search text
                # selected_item, all_cats, searchText
                q="select distinct "+selectFields+" from `"+config['catTable']+\
                "` left join `"+config['mediaTable']+"` on `"+\
                config['mediaTable']+"`.`"+config['catIDfield']+"`=`"+config['catTable']+"`.`"+config['catIDfield']+\
                "` where `"+config['catTable']+"`.`"+config['itemIDfield']+"`='"+itemID+"'"\
                " and (MATCH ("+catFullTextCols+") AGAINST ("+searchText+" "+mode+")"+\
                " or MATCH ("+mediaFullTextCols+") AGAINST ("+searchText+" "+mode+"))"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

            else:
                # the category search limited to the selected item, but not limited by search text
                # selected_item, all_cats,  NO searchText
                q="select "+selectFields+" from `"+config['catTable']+\
                "` where `"+config['catTable']+"`.`"+config['itemIDfield']+"`='"+itemID+"'"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

        else:
            if searchText:
                # the normal search limited to the selected item and selected category and searchText
                # selected_item, selected_cat,  searchText
                q="select distinct "+selectFields+" from `"+config['catTable']+\
                "` left join `"+config['mediaTable']+"` on `"+\
                config['mediaTable']+"`.`"+config['catIDfield']+"`=`"+config['catTable']+"`.`"+config['catIDfield']+\
                "` where `"+config['catTable']+"`.`"+config['catColumn']+"`='"+categoryName+"'"+\
                " and `"+config['catTable']+"`.`"+config['itemIDfield']+"`='"+itemID+"'"\
                " and (MATCH ("+catFullTextCols+") AGAINST ("+searchText+" "+mode+")"+\
                " or MATCH ("+mediaFullTextCols+") AGAINST ("+searchText+" "+mode+"))"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

            else:
                # the normal search limited to the selected item and selected category only
                # selected_item, selected_cat, NO searchText
                q="select "+selectFields+" from `"+config['catTable']+\
                "` where `"+config['catColumn']+"`='"+categoryName+"'"+\
                " and `"+config['catTable']+"`.`"+config['itemIDfield']+"`='"+itemID+"'"+\
                " order by `"+config['catTable']+"`.`"+config['catSortColumn']+"` desc"

    qresult1=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    if isinstance(qresult1,tuple):
        if itemID=='0':
            qresult2=[]
            for thisRow in qresult1:
                uniqueField=""
                row2=[thisRow[0]]
                for thisCol in range(1,len(config['itemListColumns'])+1):
                    uniqueField=uniqueField+str(thisRow[thisCol])+" "
                row2.append(uniqueField)
                for thisCol in range(len(config['itemListColumns'])+1,len(thisRow)):
                    row2.append(str(thisRow[thisCol]))
                qresult2.append(row2)
        else:
            qresult2=qresult1

        catCaption=str(len(qresult2))+' records matching search='+searchText
    else:
        # the query failed
        catCaption='No results for this search query!'
        qresult2=[]

    return (catCaption,catHeader,qresult2,"cat",q,searchMode,searchText)

def getFullTextCols(config):

    # fulltext cols for itemTable
    q="show index from `"+config['itemTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    itemFullTextCols=""
    for thisCol in qresult:
        if thisCol[10]=="FULLTEXT":
            itemFullTextCols=itemFullTextCols+"`"+config['itemTable']+'`.`'+thisCol[4]+"`,"
    itemFullTextCols=itemFullTextCols[:-1]

    # fulltext cols for catTable
    q="show index from `"+config['catTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    catFullTextCols=""
    for thisCol in qresult:
        if thisCol[10]=="FULLTEXT":
            catFullTextCols=catFullTextCols+"`"+config['catTable']+'`.`'+thisCol[4]+"`,"
    catFullTextCols=catFullTextCols[:-1]

    # fulltext cols for mediaTable
    q="show index from `"+config['mediaTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    mediaFullTextCols=""
    for thisCol in qresult:
        if thisCol[10]=="FULLTEXT":
            mediaFullTextCols=mediaFullTextCols+"`"+config['mediaTable']+'`.`'+thisCol[4]+"`,"

    mediaFullTextCols=mediaFullTextCols[:-1]

    return(itemFullTextCols,catFullTextCols,mediaFullTextCols)

def getBooleanFields(config):
    
    # for right now I'm adding all emum fields
    # perhaps I should add other fields as well

    # boolean cols for itemTable
    q="show columns from `"+config['itemTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    itemBooleanFields=""
    for thisCol in qresult:
        # add enum cols to search query to include boolean search
        if 'enum(' in thisCol[1]:
            itemBooleanFields=itemBooleanFields+",`"+config['itemTable']+"`.`"+thisCol[0]+"`"

    # boolean cols for catTable
    q="show columns from `"+config['catTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    catBooleanFields=""
    for thisCol in qresult:
        # add enum cols to boolean search
        if 'enum(' in thisCol[1]:
            catBooleanFields=catBooleanFields+",`"+config['catTable']+"`.`"+thisCol[0]+"`"

    # boolean cols for mediaTable
    q="show columns from `"+config['mediaTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    mediaBooleanFields=""
    for thisCol in qresult:
        # add enum cols to boolean search
        if 'enum(' in thisCol[1]:
            mediaBooleanFields=mediaBooleanFields+",`"+config['mediaTable']+"`.`"+thisCol[0]+"`"

    return(itemBooleanFields,catBooleanFields,mediaBooleanFields)

def searchForm(searchText,searchMode):

    moreInput=strict401gen.Input(type='checkbox',checked=searchMode,name='searchMode',id='searchMode',title="Double Quoted Boolean Search",Class="")
    searchInput=strict401gen.Input(type='text',llabel="Search",value=searchText,size="15",maxlength="20",name='searchText',id='searchText',title="Enter text to Search for.",Class="searchfield dataInput searchfieldcolor")
    searchButton=strict401gen.Input(type="image",name='searchButton',id="searchButton",srcImage="images/search2.png",alt="Search",title="Submit Search",Class="searchbutton searchSubmit")

    # the "+" sign is removed from the query text
    # I tried using enctype='multipart/form-data',but that didn't help
    # and it causes the pickle operation to fail
    form=strict401gen.Form(submit="",name='newSearch',id='newSearch',cgi='index?action=14')
    form.append(moreInput)
    form.append(searchInput)
    form.append(searchButton)

    return(form)

def moreForm():

    moreInput=strict401gen.Input(type='checkbox',name='seachMode',id='searchMode',Class="topfield")
    form=strict401gen.Form(submit="",name='moreSearch',id='moreSearch',cgi='index?action=14')
    form.append(moreInput)

    return(form)




############ item functions

def writeImgs(config):
         
    dbItemImagePath=config['itemImagePath']+config['dbname']+'/'
    
    # if the dir exists remove all files
    if os.path.exists(dbItemImagePath):
        images=os.listdir(dbItemImagePath)
        for thisimage in images:
            try:
                os.remove(dbItemImagePath+thisimage)
            except:
                pass
    else:
        # make the dir
        os.mkdir(dbItemImagePath)

    # copy the default images to the db specific dir, all images found will be copied
    images=os.listdir(config['itemImagePath'])
    for image in images:
        if os.path.isfile(config['itemImagePath']+image):
            shutil.copy(config['itemImagePath']+image,dbItemImagePath)
                
    # queyr the db for images and write all item images to disk
    q="select `"+config['itemTable']+"`.`"+config['itemIMGfield']+"`,`"\
    +config['itemTable']+"`.`"+config['itemIDfield']+"` from `"+config['itemTable']+"`"

    imageData=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    imagesondisk=[]

    # loop thru each record, attache a supported img type extension b4 writting it
    # could support other file types here in the future?
    for thisImage in imageData:
        if thisImage[0]:
            imgType=imghdr.what('',thisImage[0])
            try:
                # fix extention for windows if needed
                if len(imgType)>3:
                    imgType=imgType[0:2]+imgType[-1:]
                else:
                    imgType=imgType
                imagename=str(thisImage[1])+'.'+imgType
                imgFile=open(dbItemImagePath+imagename,"wb")
                imgFile.write(thisImage[0])
                imgFile.close()
            except:
                pass

            imagesondisk.append(str(thisImage[1])+'*'+imagename)

    return imagesondisk

def itemImg(itemImage,item,config):

    try:
        imageFiles=os.listdir(config['itemImagePath']+config['dbname'])
    except:
        imageFiles=[]

    imgName=str(item[2]).lower()
    itemImage=''

    for thisImg in imageFiles:
        fileName=thisImg.split(".")[0]
        if  imgName == fileName.lower():
            itemImage = thisImg

    if not itemImage:
        itemImage = 'default.png'

    return itemImage

def indexItem(item,itemSelected,action):

    itemCount=item[3]
    currentItem=item[5]
    itemList=item[4]

    # next item
    if action==1:
        if currentItem>=itemCount-1:
            currentItem=0
        else:
            currentItem=currentItem+1
    # prev item
    elif action==2:
        if currentItem==0:
            currentItem=itemCount-1
        else:
            currentItem=currentItem-1
    # selected item
    elif action==4 or action==0:
        if itemSelected:
            for thisItem in range(0,len(itemList)):
                if str(itemSelected) in itemList[thisItem]:
                    currentItem=thisItem
    # no change
    else:
        currentItem=item[5]


    return currentItem

def itemData(currentItem,config):

    selected=""
    for thisField in config['itemListColumns']:
        selected=selected+"`"+config['itemTable']+"`.`"+thisField+"`,"

    # get item item data
    q="select "+selected\
    +"`"+config['itemTable']+"`.`"+config['itemIDfield']+"` from `"+config['itemTable']+"`"

    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
 
    items=[]
 
    # a list of numeric ID's and a list of text with the numeric ID at the end
    for thisItem in qresult:
        items.append(list(thisItem))
 
    items.sort()
    items.reverse()
    itemList=[]
 
    # fill in a default value for empty values
    for thisItem in items:
        for thisField in range(0,len(thisItem)-1):
            if not thisItem[thisField]:
                thisItem[thisField]="Empty"
 
        itemList.append((string.join(thisItem[0:len(thisItem)-1]),str(thisItem[-1])))
 
    itemList.insert(0,("All Items","0"))
 
    ## Really need to account for zero items in table
    ## Need to branch at some point to create the first item !!!
#     mainTitle=''
#     for thisItem in range(0,len(itemList[0])-1):
#         mainTitle=mainTitle+" "+str(itemList[currentItem][thisItem])
    mainTitle=str(itemList[currentItem][0])
    itemID=itemList[currentItem][-1]
    imgName=itemList[currentItem][-1]
    itemCount=len(itemList)
 
    item=[mainTitle,itemID,imgName,itemCount,itemList,currentItem]
   
    return item
#     return mainTitle

def itemData2(itemID,config):

    selected=""
    for thisField in config['itemListColumns']:
        selected=selected+"`"+config['itemTable']+"`.`"+thisField+"`,"
#     selected=selected[:-1]
    
    # get item item data
    q="select "+selected\
    +"`"+config['itemTable']+"`.`"+config['itemIDfield']+"` from `"+config['itemTable']+"`"

    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
  
    items=[]
  
    # a list of numeric ID's and a list of text with the numeric ID at the end
    for thisItem in qresult:
        items.append(list(thisItem))
  
    items.sort()
    items.reverse()
    itemList=[]
  
    # fill in a default value for empty values
    for thisItem in items:
        for thisField in range(0,len(thisItem)-1):
            if not thisItem[thisField]:
                thisItem[thisField]="Empty"
  
        itemList.append((string.join(thisItem[0:len(thisItem)-1]),str(thisItem[-1])))
  
    itemList.insert(0,("All Items","0"))
  
    for thisItem in range(0,len(itemList)):
        if itemID in itemList[thisItem]:
            currentItem=thisItem
  
    mainTitle=''
    for thisItem in range(0,len(itemList[0])-1):
        mainTitle=mainTitle+" "+str(itemList[currentItem][thisItem])
  
    itemID=itemList[currentItem][-1]
    imgName=itemList[currentItem][-1]
    itemCount=len(itemList)
  
    item=[mainTitle,itemID,imgName,itemCount,itemList,currentItem]
 
    return item
#     return q

def itemQuery(currentItem,item,config):

    itemID=str(item[1])
    mainTitle=str(item[0])
    q="show columns from `"+config['itemTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    colNames=[]
    for thisCol in qresult:
        if 'timestamp'in thisCol[1]:
            pass
        elif 'blob' in thisCol[1]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        elif thisCol[3]=="PRI":
            idCol=thisCol[0]
        else:
            colNames.append(thisCol[0])

    colNames.insert(0,idCol)
    selectCols="`"+string.join(colNames,"`,`")+"`"

    if currentItem>0:

        # get data
        q='select '+selectCols+' from `'+config['itemTable']+'` where `'+config['itemIDfield']+'`="'+itemID+'"'
        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)

    else:

        selectCols=idCol+','+string.join(config['itemColumns'],",")
        q='select '+selectCols+' from `'+config['itemTable']+\
        '` order by `'+config['itemTable']+"`.`"+config['itemColumns'][0]+"`"

        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    # convert the results to a list of lists
    qresult=list(qresult)

    # check for notes

    q2='select `'+config['mediaTable']+'`.`'+config['itemIDfield']+'` from `'+config['mediaTable']+\
    '` left join `'+config['itemTable']+'` on `'+\
    config['mediaTable']+'`.`'+config['itemIDfield']+'`=`'+config['itemTable']+'`.`'+config['itemIDfield']+\
    '` where `'+config['itemTable']+'`.`'+config['itemIDfield'] +'`="'+str(qresult[0])+'"'

    noteID=db.dbConnect(config['selectedHost'],config['dbname'],q2,0)

    if currentItem>0:
        if qresult:
            caption='Details for '+ mainTitle
        else:
            caption='No results for this query!'
        try:
            header=[noteID[0][0]]
        except:
            header=["empty"]
    else:
        caption=''
        header=[]
        for thisName in config['itemColumns']:
            header.append(thisName.upper())

    return (caption,header,qresult,'item')

def itemAllTable(itemData,categoryName,header,colWidths,config):

    endWidth="20"

    itemTable=strict401gen.TableLite(CLASS='resultstable')
    
    if itemData:

        row='odd'

        for thisRecord in itemData:

            if row=='odd':
                row='even'
            else:
                row='odd'

            itemRow=strict401gen.TR(Class=row+"row")
            recNum=''

            # get note data
            q2='select `'+config['mediaTable']+'`.`'+config['mediaIDfield']+'` from `'+config['mediaTable']+\
            '` left join `'+config['itemTable']+'` on `'+\
            config['mediaTable']+'`.`'+config['itemIDfield']+'`=`'+config['itemTable']+'`.`'+config['itemIDfield']+\
            '` where `'+config['itemTable']+'`.`'+config['itemIDfield']+'`="'+str(thisRecord[0])+'"'

            noteID=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
            try:
                note=noteID[0]
            except:
                note=""

            for thisCol in range(0,len(thisRecord)):

                if thisCol==0:
                    recNum=str(thisRecord[thisCol])
                    gotoImage=strict401gen.Image(("images/left2.png","16","16"),alt="Goto",id="goto",title="Goto Item Record")
                    itemRow.append(strict401gen.TD(strict401gen.Href("index?item="+str(thisRecord[thisCol]),gotoImage),Class="resultcol0"))

                elif thisRecord[thisCol]:
                    itemRow.append(strict401gen.TD(thisRecord[thisCol],Class="resultcol"))
                else:
                    itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),Class="resultcol"))

            if not note:
                noteimage=strict401gen.Image(("images/add.png","16","16"),alt="Add",title="Add a "+config['mediaTable'])
                itemRow.append(strict401gen.TD(strict401gen.Href("index?media=Inew"+recNum,noteimage),Class="resultcol"))
            else:
                noteimage=strict401gen.Image(("images/right2.png","16","16"),id=str(thisRecord[0]),alt='View',title="View "+config['mediaTable'])
                itemRow.append(strict401gen.TD(strict401gen.Href("index?media=I"+recNum,noteimage),Class="resultcol"))

            itemTable.append(itemRow)

        # last row first col
        itemRow=strict401gen.TR()
        itemRow.append(strict401gen.TH(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="")))
        # last row middle cols
        for thisCol in colWidths:
            itemRow.append(strict401gen.TH(strict401gen.Image(("images/shim.gif",str(int(thisCol)-2),"10"),alt="")))
        # last row last col
        itemRow.append(strict401gen.TH(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="")))
        itemTable.append(itemRow)

    else:
        row='odd'
        itemRow=strict401gen.TR(Class=row+"row")
        
        if itemData:
            itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="1"))
        else:
            itemRow.append(strict401gen.TD(strict401gen.RawText("No records found "),colspan="1"))
        itemTable.append(itemRow)

    return itemTable

def itemTable(itemID,itemData,config):

    q="show columns from `"+config['itemTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    colNames=[]
    for thisCol in qresult:
        if 'timestamp'in thisCol[1]:
            pass
        elif 'blob' in thisCol[1]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        elif thisCol[3]=="PRI":
            idCol=thisCol[0]
        else:
            colNames.append(thisCol[0])

    colNames.insert(0,idCol)

    catSums=catSum(itemID,config)
    for thisSum in catSums:
        colNames.append(thisSum[0])
        itemData.append(thisSum[1])

    if itemData:

        resultTable=strict401gen.TableLite()
        row='odd'

        for thisCol in range(1,len(colNames)):
            if row=='odd':
                row='even'
            else:
                row='odd'

            itemRow=strict401gen.TR(Class=row+'row')
            itemRow.append(strict401gen.TD(colNames[thisCol],style="width:385px;"))
                            
            if itemData[thisCol]:
                if colNames[thisCol] in config['supportTables']:
                    titleData=getToolTip(colNames[thisCol],itemData[thisCol],config)
                    itemRow.append(strict401gen.TD(itemData[thisCol],title=titleData,Class='supportTootTip'))                    
                else:
                    itemRow.append(strict401gen.TD(itemData[thisCol],style="width:383px;"))
            else:
                itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),style="height:5mm;width:400px;"))

            resultTable.append(itemRow)
    else:
        # the query failed
        row='odd'
        resultTable=strict401gen.TableLite()
        itemRow=strict401gen.TR(Class=row+'row')
        itemRow.append(strict401gen.TD('No query results.',style="width:383px;"))
        itemRow.append(strict401gen.TD(str(q),style="width:383px;"))

        resultTable.append(itemRow)

    return (resultTable)

def itemForm(itemList,currentItem):
#     itemList2=strict401gen.Select(itemList,onChange="javascript:this.form.submit();",size=1,name='item',id='item',selected=itemList[currentItem],Class="topfield")

    itemList2=strict401gen.Select(itemList,zebra='on',onChange="javascript:document.newItem.submit();",size=1,name='item',id='item',selected=itemList[currentItem],Class="topfield")
    form=strict401gen.Form(submit="",name='newItem',id='newItem',cgi='index?action=4')
    form.append(itemList2)

    return(form)

def createItem(currentItem,item,config):

    cols=[]
    colNames=[]

    q="show columns from `"+config['itemTable']+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in allCols:
        if thisCol[0] in config['primaries']:
            pass
        elif 'timestamp' in thisCol[1]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        else:
            cols.append(thisCol)
            colNames.append(thisCol[0])

    itemTable=strict401gen.TableLite(Class="edittable edittablecolor")

    # semicolons not passed, string will break at semicolon
    count=0
    itemRow=strict401gen.TR()

    for thisField in cols:
        try:
            fieldlen=thisField[1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

        count=count+1

        if 'enum(' in thisField[1]:
            enumList=thisField[1].split(",")
            enumList[0]=enumList[0][5:]
            enumList[len(enumList)-1]=enumList[len(enumList)-1][:-1]
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Select(enumList,name=thisField[0],id=thisField[0],Class="editfield")))

        elif 'set(' in thisField[1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][4:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],id=thisField[0],multiple=1,size=len(setList),Class="editfield")))

        elif 'date' in thisField[1]:
            x=string.strip(str(datetime.date.today()))
            itemRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=thisField[0],id=thisField[0],maxlength="10",Class="editfield dataInput")))

        elif 'text' in thisField[1]:
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Textarea(name=thisField[0],id=thisField[0],Class="editfield dataInput")))

        elif 'blob' in thisField[1]:
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Input(type='file',name=thisField[0],id=thisField[0],size="10",Class="editfield")))

        elif thisField[0] in config['supportTables']:
            #we have a support table, used to generate a selecet field
            shortList,longList=getPickList(thisField[0],config)
#             test=str(cols[thisField][0])+"  short: "+str(shortList)+"   long: "+str(longList)
            itemRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Select(shortList,name=thisField[0],id=thisField[0],Class="editfield")))            

        else:
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],id=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            itemTable.append(itemRow)
            itemRow=strict401gen.TR()
        elif count==len(cols):
            itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2"))
            itemTable.append(itemRow)

    caption='Insert the information for new "'+config['dbname']+'" item'
    header=formbuttons('create')

    return (caption,header,itemTable,'item')

def editItem(currentItem,item,config):

    itemID=str(item[1])
    cols=[]
    colNames=[]

    # get the column  names
    q="show columns from `"+config['itemTable']+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in allCols:
        if thisCol[0] in config['primaries']:
            pass
        elif 'timestamp' in thisCol[1]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        else:
            cols.append(thisCol)
            colNames.append(thisCol[0])

    selectCols="`"+string.join(colNames,"`,`")+"`"
    q='select '+selectCols+' from `'+config['itemTable']+\
    '` where `'+config['itemIDfield']+'`="'+itemID+'"'
    values=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    itemTable=strict401gen.TableLite(Class="edittable edittablecolor")

    # semicolons not passed, string will break at semicolon
    count=0
    itemRow=strict401gen.TR()

    for thisField in range(0,len(cols)):
        try:
            fieldlen=cols[thisField][1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

        count=count+1

        if 'enum(' in cols[thisField][1]:
            enumList=cols[thisField][1].split(",")
            enumList[0]=enumList[0][5:]
            enumList[len(enumList)-1]=enumList[len(enumList)-1][:-1]
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))

        elif 'set(' in cols[thisField][1]:
            setList=cols[thisField][1].split(",")
            setList[0]=setList[0][4:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Select(setList,name=cols[thisField][0],id=cols[thisField][0],multiple=1,size=len(setList),Class="editfield")))

        elif 'text' in cols[thisField][1]:
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Textarea(values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield dataInput")))

        elif 'date' in cols[thisField][1]:
            if not values[0][thisField] or values[0][thisField]=="None":
                x=string.strip(str(datetime.date.today()))
            else:
                x=values[0][thisField]
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=cols[thisField][0],id=cols[thisField][0],maxlength="10",Class="editfield dataInput")))

        elif 'blob' in cols[thisField][1]:
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],id=cols[thisField][0],size="10",Class="editfield")))

        elif cols[thisField][0] in config['supportTables']:
            #we have a support table, used to generate a selecet field
            shortList,longList=getPickList(cols[thisField][0],config)
#             test=str(cols[thisField][0])+"  short: "+str(shortList)+"   long: "+str(longList)
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            if not values[0][thisField] or values[0][thisField]=="None":
                itemRow.append(strict401gen.TD(strict401gen.Select(shortList,name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))            
            else:
                itemRow.append(strict401gen.TD(strict401gen.Select(shortList,selected=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))            

        else:
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            itemTable.append(itemRow)
            itemRow=strict401gen.TR()
        elif count==len(cols):
            itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
            itemTable.append(itemRow)

    caption='Update  the information for "'+config['dbname']+'"'
    header=formbuttons('update')

    return (caption,header,itemTable,'item')

############ category functions

def catSum(currentItem,config):
    numericTypes=('int','tinyint','smallint','medint','bigint','integer','real','double','float','decimal','numeric')
    q="show columns from `"+config['catTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    colSums=[]
    for thisCol in qresult:
        colType=thisCol[1].partition('(')
        colName=thisCol[0]
        if colType[0] in numericTypes:
            q1="select sum(`"+colName+"`) from `"+config['catTable']+"` where `"+config['itemIDfield']+"`="+str(currentItem)
            qresult=db.dbConnect(config['selectedHost'],config['dbname'],q1,0)
            if colName[0]!="_":

                colValue=qresult[0][0]
                if colValue:
                    colValue=str(int(colValue))
                else:
                    colValue="0"

                colSums.append(["Total for "+colName,colValue])
#                colSums.append(q1)
    return colSums

def catImgs(config):

    categoryImagePath=config['catImagePath']+config['dbname']+'/'
    
    if os.path.exists(categoryImagePath):
        images=os.listdir(categoryImagePath)
    else:
        # get the default images
        images=os.listdir(config['catImagePath'])
        os.mkdir(categoryImagePath)
        for image in images:
            if os.path.isfile(config['catImagePath']+'/'+image):
                shutil.copy(config['catImagePath']+'/'+image,categoryImagePath)
        images=os.listdir(categoryImagePath)
        
    cats=[]
    catImages=[]

    q='describe `'+config['catTable']+'` `'+config['catColumn']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
    catstrings=string.split(qresult[1],",")

    # extract the cat name from the enum field
    for thisCat in catstrings:
        catName=thisCat.replace("'","")
        catName=catName.replace("enum(","")
        catName=catName.replace(")","")
        cats.append(catName)

    for thisCat in range(0,len(cats)):
        found=0
        for thisImage in images:
            if cats[thisCat] in thisImage:
                catImages.append((cats[thisCat],thisImage))
                found=1
        if not found:
            catImages.append((cats[thisCat],'default'+str(thisCat)+'.jpg'))

    catImages.sort()
    if 'All_Records.png' in images:
        catImages.insert(0,("All Records","All_Records.png"))
    else:
        catImages.insert(0,("All Records","default.png"))

    return catImages

def catImgs2(config):
    
    # a default list of one tuple will be used
    # an 'All Records' category is supplied with the default image
    # seems like it would not have to be in the category table, except to be able to change the image.
    # and so if a record is found with the category name of 'All Records' it's image will be used.
    # the text 'All' at the beginning of a category has special meaning in the script and will allways
    # provide a 'select *' sql, so don't use that text unless you want unpredictable results.

    catImages=[]
    categoryImagePath=config['catImagePath']+config['dbname']+'/'
    allRecordsImageName='default.png'
    
    q="SELECT * FROM `"+config['dbname']+"`.`_category`;"
    categoryData=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    if categoryData:
        # loop thru each record, write the img to disk
        for thisRow in categoryData:
            try:
                # this will fail if there isn't an image name stored
                # which will happen if there isn't an image stored
                # the result will be that this category will not show up in the list
                
                fileExt=thisRow[3].split(".")[1]
                imageName=str(thisRow[1])+'.'+fileExt
                imgFile=open(categoryImagePath+imageName,"wb")
                imgFile.write(thisRow[2])
                imgFile.close()
                if thisRow[1]=='All Records':
                    allRecordsImageName=imageName
                elif thisRow[1]=='default':
                    pass
                else:
                    catImages.append((thisRow[1],imageName))
    
            except:
                pass
            
            
        catImages.sort()
        catImages.insert(0,('All Records',allRecordsImageName))

    
    else:
        # no data in category table, default to:
        catImages.append(('All Records',allRecordsImageName))
    

    return catImages

def indexCat(currentCat,catImages,catSelected,action):

    catCount=len(catImages)
    if action==5:
        # next cat
        if currentCat>=catCount-1:
            currentCat=0
        else:
            currentCat=currentCat+1
    elif action==6:
        # prev cat
        if currentCat==0:
            currentCat=catCount-1
        else:
            currentCat=currentCat-1
    # selected cat
    elif action==8:
        for thisImage in range(0,len(catImages)):
            if catSelected in catImages[thisImage][1]:
                currentCat=thisImage

    return currentCat

def catQuery(req,categoryName,itemID,config):

    selectFields,catHeader=catColumns(categoryName,itemID,config)

    if itemID=='0':
        if categoryName[:3]=='All': # will NOT show results
            # get all records for all items
            # all_items, all_cats, NO searchText
            q='select '+selectFields+' from `'+config['catTable']+\
            '` left join `'+config['itemTable']+'` on `'+\
            config['catTable']+'`.`'+config['itemIDfield']+\
            '`=`'+config['itemTable']+'`.`'+config['itemIDfield']+\
            "` order by `"+config['catTable']+'`.`'+config['catSortColumn']+"` desc"

        else:
            # get records in this category all items
            q='select '+selectFields+' from `'+config['catTable']\
            +'` left join `'+config['itemTable']+'` on `'\
            +config['catTable']+'`.`'+config['itemIDfield']+'`=`'+config['itemTable']+'`.`'+config['itemIDfield']\
            +'` where `'+config['catColumn']+'`="'+categoryName+'"'\
            +" order by `"+config['catTable']+'`.`'+config['catSortColumn']+"` desc"

    else:
        if categoryName[:3]=='All':
            # get all records
            q='select '+selectFields+' from `'+config['catTable']\
            +'` where `'+config['catTable']+'`.`'+config['itemIDfield']+'`="'+itemID+'"'\
            +" order by `"+config['catTable']+'`.`'+config['catSortColumn']+"` desc"
        else:
            # get records in this category this item only
            q='select '+selectFields+' from `'+config['catTable']\
            +'` where `'+config['catColumn']+'`="'+categoryName+'"'\
            +' and `'+config['catTable']+'`.`'+config['itemIDfield']+'`="'+itemID+'"'\
            +" order by `"+config['catTable']+'`.`'+config['catSortColumn']+"` desc"

    qresult1=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
 
    if itemID=='0':
        qresult2=[]
        for thisRow in qresult1:
            uniqueField=""
            row2=[thisRow[0]]
            for thisCol in range(1,len(config['itemListColumns'])+1):
                uniqueField=uniqueField+str(thisRow[thisCol])+" "
            row2.append(uniqueField)
            for thisCol in range(len(config['itemListColumns'])+1,len(thisRow)):
                row2.append(str(thisRow[thisCol]))
            qresult2.append(row2)
    else:
        qresult2=qresult1
 
    if isinstance(qresult1,tuple):
        catCaption=str(len(qresult1))+' records matching "'+categoryName+'"'
    else:
        catCaption='No results for this query!'
        catHeader=[]

    return (catCaption,catHeader,qresult2,'cat')
#     return (q)

def catTable(catData,categoryName,header,colWidths,config):
    
    q="show columns from `"+config['catTable']+"`"
    cols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    endWidth="20"

    if config['itemTable'].upper() in header:
        searchType='booleanSearch'
    elif config['catColumn'].upper() in header:
        searchType='allSearch'
    else:
        searchType=''

    catTable=strict401gen.TableLite(CLASS='resultstable')

    if catData:

        row='odd'
        for thisRecord in catData:

            if row=='odd':
                row='even'
            else:
                row='odd'


            catRow=strict401gen.TR(Class=row+'row')
            recNum=''

            # get note data
            q2='select `'+config['mediaTable']+'`.`'+config['mediaIDfield']+'` from `'+config['mediaTable']+\
            '` left join `'+config['catTable']+'` on `'+\
            config['mediaTable']+'`.`'+config['catIDfield']+'`=`'+config['catTable']+'`.`'+config['catIDfield']+\
            '` where `'+config['catTable']+'`.`'+config['catIDfield']+'`="'+str(thisRecord[0])+'"'

            noteID=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)

            editImg="images/edit.png"
            editToolTip="Edit Record"            
            try:
                note=noteID[0]
                deleteImg="images/delete-inactive.png"
                delToolTip="Other records depend on this record"
            except:
                note=""
                deleteImg="images/delete.png"
                delToolTip="Delete Record"
            if config['login']=='':
                editImg="images/edit-inactive.png"
                editToolTip="Not logged in"
                deleteImg="images/delete-inactive.png"
                delToolTip="Not logged in"                

            for thisCol in range(0,len(thisRecord)):

                if thisCol==0:
                    recNum=str(thisRecord[thisCol])

                    toolTable=strict401gen.TableLite(CLASS='tooltable')
                    toolRow=strict401gen.TR(Class=row+'row')
                    # column for the edit button
#                     if searchType=='booleanxSearch':
#                         editImage=strict401gen.RawText("&nbsp;")
#                     elif searchType=="allSearch":
#                         editImage=strict401gen.Image(("images/edit.png","16","16"),alt="Edit",id="Edit",title="Edit Record")
#                     else:
                    editImage=strict401gen.Image((editImg,"16","16"),alt="Edit",id="Edit",title=editToolTip)
                    if 'inactive'in editImg:
                        toolRow.append(strict401gen.TD(editImage))
                    else:
                        toolRow.append(strict401gen.TD(strict401gen.Href("index?edit="+str(thisRecord[thisCol]),editImage),colspan="1",Class="toolcol0"))
                    toolTable.append(toolRow)
                    toolRow=strict401gen.TR(Class=row+'row')

                    # column for the delete link
                    delimage=strict401gen.Image((deleteImg,str(endWidth),str(endWidth)),alt="Del",id="Del",title=delToolTip)
                    if delToolTip:
                        toolRow.append(strict401gen.TD(strict401gen.Href("index?popup=96&amp;catID="+str(thisRecord[thisCol]),delimage),colspan="1",Class="toolcol0"))
                    else:
                        toolRow.append(strict401gen.TD(delimage,colspan="1",Class="toolcol0"))
                    toolTable.append(toolRow)
                    catRow.append(strict401gen.TD(toolTable,colspan="1",Class="toolcol0"))

                elif thisRecord[thisCol]:
                    
                    if header[thisCol-1].lower() in config['supportTables']:
                        titleData=getToolTip(header[thisCol-1].lower(),thisRecord[thisCol],config)
                        catRow.append(strict401gen.TD(thisRecord[thisCol],title=titleData,Class='supporttooltip'))
                    else:
                        catRow.append(strict401gen.TD(thisRecord[thisCol],Class="resultcol"))
                else:
                    catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),Class="resultcol"))
#                     catRow.append(strict401gen.TD(str(config['supportTables']),Class="resultcol"))

            if not note:
                noteimage=strict401gen.Image(("images/add.png","16","16"),alt="Add",title="Add a "+config['mediaTable'])
                catRow.append(strict401gen.TD(strict401gen.Href("index?media=new"+recNum,noteimage),Class="resultcol"))
            else:
                noteimage=strict401gen.Image(("images/right2.png","16","16"),id=str(thisRecord[0]),alt='View',title="View "+config['mediaTable'])
                catRow.append(strict401gen.TD(strict401gen.Href("index?media="+recNum,noteimage),Class="resultcol"))

            catTable.append(catRow)

        # last row first col
        catRow=strict401gen.TR()
        catRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="Edit")))
        # last row middle cols
        for thisCol in colWidths:
            catRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",str(int(thisCol)-2),"10"),alt="Edit")))
        # last row last col
        catRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="Edit")))
        catTable.append(catRow)

    else:
        row='odd'

        catRow=strict401gen.TR(Class=row+'row')
        if catData:
            catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="1"))
        else:
            catRow.append(strict401gen.TD(strict401gen.RawText("No records found for "+categoryName),colspan="1"))
        catTable.append(catRow)
        
#     return catData
    return catTable

def catColumns(categoryName,itemID,config):

    colNames=[]
    selectFields=''
    catHeader=[]

    q="show columns from `"+config['catTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    # filter out certain cols
    for thisCol in qresult:
        if 'timestamp'in thisCol[1]:
            pass
        elif 'text' in thisCol[1]:   # why???
            pass
        elif thisCol[3]=="PRI":
            idCol=thisCol[0]
        elif thisCol[0] in config['primaries']:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        else:
            colNames.append(thisCol[0])

    colNames.insert(0,idCol)

    if itemID=='0':
        if categoryName[:3]=="All":
            # header for all items, all categories
            catHeader=[config['itemTable'].upper()]
            for thisField in config['catSearchColumns']:
                catHeader.append(thisField.upper())

            # selected fields for all items, all categories
            selectFields="`"+config['catTable']+"`.`"+config['catIDfield']+"`,"
            for thisCol in config['itemListColumns']:
                selectFields=selectFields+"`"+config['itemTable']+'`.`'+thisCol+"`,"
            for thisCol in config['catSearchColumns']:
                selectFields=selectFields+"`"+config['catTable']+'`.`'+thisCol+"`,"
                
            selectFields=selectFields[:-1]

        else:
            if config['catColumn'] in config['catSearchColumns']:
                config['catSearchColumns'].remove(config['catColumn'])

            # header for all items, one category
            catHeader=[config['itemTable'].upper()]
            for thisField in config['catSearchColumns']:
                catHeader.append(thisField.upper())

            # selected fields for all items, one category
            selectFields="`"+config['catTable']+"`.`"+config['catIDfield']+"`,"
            for thisCol in config['itemListColumns']:
                selectFields=selectFields+"`"+config['itemTable']+'`.`'+thisCol+"`,"
            for thisCol in config['catSearchColumns']:
                selectFields=selectFields+"`"+config['catTable']+'`.`'+thisCol+"`,"
            selectFields=selectFields[:-1]

    else:
        if categoryName[:3]=='All':
            # header for one item, all categories
            for thisCol in range(1, len(colNames)):
                catHeader.append(colNames[thisCol].upper())

            # selected fields for one item, all categories
            for thisCol in colNames:
                selectFields=selectFields+"`"+config['catTable']+'`.`'+thisCol+"`,"
            selectFields=selectFields[:-1]

        else:
            if config['catColumn'] in colNames:
                colNames.remove(config['catColumn'])

            # header for one item, one categories
            for thisCol in range(1, len(colNames)):
                catHeader.append(colNames[thisCol].upper())

            # selected fields for one item, one category
            for thisCol in colNames:
                selectFields=selectFields+"`"+config['catTable']+'`.`'+thisCol+"`,"
            selectFields=selectFields[:-1]

    return (selectFields,catHeader)

def catForm(catImages,currentCat):

    catList=strict401gen.Select(catImages,zebra='on',onChange="javascript:document.newCat.submit();",size=1,name='category',id='category',selected=catImages[currentCat],Class="topfield")
    form=strict401gen.Form(submit="",name='newCat',id='newCat',cgi='index?action=8')
    form.append(catList)

    return(form)

def createCat(categoryName,item,config):

    cols=[]

    q="show columns from `"+config['catTable']+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in allCols:
        if thisCol[0] in config['primaries']:
            pass
        elif 'timestamp' in thisCol[1]:
            pass
        elif config['catColumn'] in thisCol[0]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        else:
            cols.append(thisCol)

    catTable=strict401gen.TableLite(Class="edittable edittablecolor")

    count=0
    catRow=strict401gen.TR()

    for thisField in cols:
        try:
            fieldlen=thisField[1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

        count=count+1

        if 'enum(' in thisField[1]:
            enumList=thisField[1].split("','")
            enumList[0]=enumList[0][6:]
            enumList[len(enumList)-1]=enumList[len(enumList)-1][:-2]
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(enumList,name=thisField[0],id=thisField[0],Class="editfield")))

        elif 'set(' in thisField[1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],id=thisField[0],multiple=1,size=len(setList),Class="editfield")))

        elif 'text' in thisField[1]:
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Textarea(name=thisField[0],id=thisField[0],Class="editfield dataInput")))

        elif 'blob' in thisField[1]:
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type='file',name=thisField[0],id=thisField[0],Class="editfield")))

        elif 'date' in thisField[1]:
            x=string.strip(str(datetime.date.today()))
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=thisField[0],id=thisField[0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in thisField[1]:
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],id=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        elif 'float' in thisField[1]:
            maxlen=maxlen.split(',')[0]
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],id=thisField[0],maxlength="6",Class="editfield dataInput")))

        elif thisField[0] in config['supportTables']:
            #we have a support table, used to generate a selecet field
            shortList,longList=getPickList(thisField[0],config)
#             test=str(cols[thisField][0])+"  short: "+str(shortList)+"   long: "+str(longList)
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(shortList,name=thisField[0],id=thisField[0],Class="editfield")))            

        else: # char fields
            if thisField[4]:
                defaultValue=thisField[4]
            else:
                defaultValue=''
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(value=defaultValue,type="text",name=thisField[0],id=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            catTable.append(catRow)
            catRow=strict401gen.TR()
        elif count==len(cols):
            catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
            catTable.append(catRow)

    caption='Insert the information for "'+categoryName+'" '+config['catTable']
    header=formbuttons('create')

    return (caption,header,catTable,'cat')

def editCat(categoryName,catID,config):

    cols=[]
    colNames=[]
    relatedName="This Record"
    test=''
    
    # get the column  names
    q="show columns from `"+config['catTable']+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    if categoryName[:3]=='All':
        for thisCol in allCols:
            if thisCol[0] in config['primaries']:
                pass
            elif 'timestamp' in thisCol[1]:
                pass
            else:
                cols.append(thisCol)
                colNames.append(thisCol[0])
    else:
        for thisCol in allCols:
            if thisCol[0] in config['primaries']:
                pass
            elif 'timestamp' in thisCol[1]:
                pass
            elif config['catColumn'] in thisCol[0] :
                pass
            elif config['owner'] in thisCol[0]:
                pass
            else:
                cols.append(thisCol)
                colNames.append(thisCol[0])

    # get col values
    selectCols="`"+string.join(colNames,"`,`")+"`"
    q="select "+selectCols+" from `"+config['catTable']+\
    "` where `"+config['catIDfield']+"`='"+catID+"'"
    values=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    catTable=strict401gen.TableLite(Class="edittable edittablecolor")

    count=0
    catRow=strict401gen.TR()

    for thisField in range(0,len(cols)):
        try:
            fieldlen=cols[thisField][1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

        count=count+1

        if 'enum(' in cols[thisField][1]:
            enumList=cols[thisField][1].split("','")
            enumList[0]=enumList[0][6:]
            enumList[len(enumList)-1]=enumList[len(enumList)-1][:-2]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))

        elif 'set(' in cols[thisField][1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(setList,name=cols[thisField][0],id=thisField[0],multiple=1,size=len(setList),Class="editfield")))

        elif 'text' in cols[thisField][1]:
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Textarea(values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield dataInput")))

        elif 'blob' in cols[thisField][1]:
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))

        elif 'date' in cols[thisField][1]:
            if not values[0][thisField] or values[0][thisField]=="None":
                x=string.strip(str(datetime.date.today()))
            else:
                x=values[0][thisField]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=cols[thisField][0],id=cols[thisField][0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in cols[thisField][1]:
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        elif 'float' in cols[thisField][1]:
            maxlen=maxlen.split(',')[0]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        elif colNames[thisField] in config['supportTables'] or colNames[thisField]==config['catColumn']:
            #we have a support table, used to generate a select field
            shortList,longList=getPickList(cols[thisField][0],config)
#             test=str(cols[thisField][0])+"  short: "+str(shortList)+"   long: "+str(longList)
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            if not values[0][thisField] or values[0][thisField]=="None":            
                catRow.append(strict401gen.TD(strict401gen.Select(shortList,name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))            
            else:
                catRow.append(strict401gen.TD(strict401gen.Select(shortList,selected=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))
            
        else: # char fields
            if cols[thisField][0][-1]=="_":
                relatedName=values[0][thisField]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))
                
        if not count%2:
            catTable.append(catRow)
            catRow=strict401gen.TR()
        elif count==len(cols):
            catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
            catTable.append(catRow)

    caption='Update the information for "'+relatedName+'"'
    header=formbuttons('update')

    return (caption,header,catTable,'cat',repr(cols))


############ media functions

def mediaQuery(record,config):

    q="show columns from `"+config['mediaTable']+"`"
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    colNames=[]
    orderby=''

    for thisCol in qresult:
        if 'timestamp'in thisCol[1]:
            pass
        elif thisCol[3]=='PRI':
            idCol=thisCol[0]
        elif thisCol[0] in config['primaries']:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        elif config['invisible'] in thisCol[0]:
            pass
        else:
            if 'date'in thisCol[1]:
                orderby=thisCol[0]
            colNames.append(thisCol[0])
    colNames.insert(0,idCol)    # for edit link

    # build the select fields for the media table query
    selectFields=""
    for thisField in colNames:
        selectFields=selectFields+"`"+config['mediaTable']+'`.`'+thisField+'`,'
    selectFields=selectFields[:-1]

    if record[0]=="I":
        # this is an item note
        recordNum=record[1:]
        q='select '+selectFields +' from `'+config['mediaTable']+\
        '` where `'+config['mediaTable']+'`.`'+config["itemIDfield"]+'`="'+recordNum+'"'
    else:
        # this is a category note
        recordNum=record
        q='select '+selectFields +' from `'+config['mediaTable']+\
        '` where `'+config['mediaTable']+'`.`'+config["catIDfield"]+'`="'+recordNum+'"'

    if orderby:
        q=q+" order by `"+config['mediaTable']+"`.`"+orderby+"` desc"


    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    if record[0]=="I":
        # for an item caption
        q2='select `'+string.join(config['itemListColumns'],"`,`")+'` from `'+\
        config['itemTable']+'` where `'+ config['itemIDfield']+'`="'+recordNum+'"'

        header=db.dbConnect(config['selectedHost'],config['dbname'],q2,0)
        #~ mediaCaption=config['mediaTable']+'(s) for '+string.join(header[0]," ")
        mediaCaption=string.join(header[0]," ")
        mediaHeader=['Imedia']

    else:
        # for a category header
        q2='select `'+config['catInfoColumn']+'` from `'+\
        config['catTable']+'` where `'+ config['catIDfield']+'`="'+recordNum+'"'

        header=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
        #~ mediaCaption=config['mediaTable']+'(s) for '+header[0]+' '
        mediaCaption=header[0]+' '
        mediaHeader=['media']

    return (mediaCaption,mediaHeader,qresult,'media')

def mediaTable(mediaData,cookieID,record,config):
    
    test=''
    fileType=''
    filename=''
    blobToolTip=''
    fieldTypes=[]
    fieldNames=[]
    isBlob=0
    isImg=""
    isText=0
    endWidth=16
    
    mediaTable=strict401gen.TableLite(CLASS='mediatable')
    
    # get a list of the fieltypes so I can branch on blob fields
    q="show columns from `"+config['mediaTable']+"`"
    cols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in cols:
        fieldNames.append(thisCol[0])
        fieldTypes.append(thisCol[1])

    row='odd'
    imageCount=0
    
    for thisRow in mediaData:

        # display the owner at the top of the media if available
        # enabled for the 'read' db specifically
        if record[0]=="I":
            # this is an item note
            q='select `'+config['owner'] +'` from `'+config['mediaTable']+\
            '` where `'+config['mediaTable']+'`.`'+config["mediaIDfield"]+'`="'+str(thisRow[0])+'"'
        else:
            # this is a category note
            q='select `'+config['owner']+'` from `'+config['mediaTable']+\
            '` where `'+config['mediaTable']+'`.`'+config["mediaIDfield"]+'`="'+str(thisRow[0])+'"'

        owner=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        # try will fail if the table doesn't have an owner field
        try:
            owner=owner[0]
        except:
            owner=''

        if row=='odd':
            row='even'
        else:
            row='odd'

        # check to see if it's an Item record
        q="select `"+config['itemIDfield']+"` from `"+config['mediaTable']+\
        "` where `"+config['mediaIDfield']+'`="'+str(thisRow[0])+'"'

        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        if qresult[0]:
            mediaType="I"
        else:
            mediaType=""

        mediaRow=strict401gen.TR(Class=row+'row')
        charTable=strict401gen.TableLite(CLASS='mediacoltext')
        rowHasBinaryData='yes'

        for thisCol in range(0,len(thisRow)):
            if 'blob' in fieldTypes[thisCol]:
                try:
                    x=len(thisRow[thisCol])
                except:
                    rowHasBinaryData='no'

        # go through the cols, insert the data into the table
        for thisCol in range(0,len(thisRow)):
    
            # if this col is an image set the image type
            try:
                isImg="."+imghdr.what('',thisRow[thisCol])
                if isImg not in (".png",".jpeg",".gif",".bmp"):
                    isImg=''
            except:
                isImg=''
                
            # if this col is a blob supply a icon and link
            if 'blob' in fieldTypes[thisCol]:
                isBlob=1
                q='select `'+config['mediaTable']+'`.`'+config['invisible']+'` from `'+config['mediaTable']+'`'+\
                ' where `'+config['mediaTable']+'`.`'+config["mediaIDfield"]+'`'+'="'+str(thisRow[0])+'"'
                qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
                test=test+"***************"+str(q)
                try:
                    filename=qresult[0]
                except:
                    filename=''
                if filename:
                    fileType=getFileType2(filename)
                    iconName=fileType+".png"
                    if fileType=="unknown":
                        blobToolTip="This is an unknown file type."
                    else:
                        blobToolTip="This is a "+fileType+" file."
                else:
                    isBlob=0
            else:
                isBlob=0
            
            if "text" in fieldTypes[thisCol]:
                isText=1
            else:
                isText=0
                
            test="fieldtypes "+str(fieldTypes)+"fieldNames "+str(fieldNames)
    
    
            if thisCol==0:
        
                editImg="images/edit.png"
                editToolTip="Edit Record"            
                deleteImg="images/delete.png"
                delToolTip="Delete Record"
                if config['login']=='':
                    editImg="images/edit-inactive.png"
                    editToolTip="Not logged in"
                    deleteImg="images/delete-inactive.png"
                    delToolTip="Not logged in"                

                
                toolTable=strict401gen.TableLite(CLASS='tooltable')
                # column for the edit button if not a All search
                toolRow=strict401gen.TR(Class=row+'row')
                editimage=strict401gen.Image((editImg,str(endWidth),str(endWidth)),alt="Edit",id="Edit",title=editToolTip)
                if 'inactive' in editImg:
                    toolRow.append(strict401gen.TD(editimage,Class="meidiacoltools"))
                else:
                    toolRow.append(strict401gen.TD(strict401gen.Href("index?medit="+mediaType+str(thisRow[thisCol]),editimage),colspan="1",Class="meidiacoltools"))
                toolTable.append(toolRow)
                # column for the delete button if not a All search
                toolRow=strict401gen.TR(Class=row+'row')
                delimage=strict401gen.Image((deleteImg,str(endWidth),str(endWidth)),alt="Del",id="Del",title=delToolTip)
                if 'inactive' in deleteImg:
                    toolRow.append(strict401gen.TD(delimage,Class="meidiacoltools"))
                else:
                    toolRow.append(strict401gen.TD(strict401gen.Href("index?popup=97"+"&amp;mediaID="+str(thisRow[thisCol])+"&amp;media="+str(record),delimage),colspan="1",Class="meidiacoltools"))
                toolTable.append(toolRow)
                # add the buttons at col one
                mediaRow.append(strict401gen.TD(toolTable,colspan="1",Class="meidiacoltools"))
                # add the charTable for a verticle list of character fields
                mediaRow.append(strict401gen.TD(charTable,colspan="1",Class="meidiacoltext"))
    
            elif isImg:
                # if it's an image write it to disk so the program can load it
                if os.path.exists(config['mediaPath']+cookieID):
                    pass
                else:
                    os.mkdir(config['mediaPath']+cookieID)
                imageCount=imageCount+1
                # imagename must be unique
                imagename=config['dbname']+'-'+str(thisRow[0])+'-'+str(imageCount)+isImg
                imgFile=open(config['mediaPath']+cookieID+'/'+imagename,"wb")
                imgFile.write(thisRow[thisCol])
                imgFile.close()
    
                imageLink=strict401gen.Href("tmp/"+cookieID+'/'+imagename,strict401gen.Image("tmp/"+cookieID+'/'+imagename,title="Click to view full size image",alt="This is a "+isImg+" file.",Class="mediacolimage"),onClick="window.open(this.href);return false;")
                mediaRow.append(strict401gen.TD(imageLink,colspan="1",Class="mediacolimage"))
    
            elif isBlob:
                # this is a minimal branching for binary files not recognized as images
                # I've read that it gives false results for utf16 files, possibly other files too.
                # I just provide a icon that allows downloading of the data.
                
                if os.path.exists(config['mediaPath']+cookieID):
                    pass
                else:
                    os.mkdir(config['mediaPath']+cookieID)
                imageCount=imageCount+1
                # name must be unique
                blobName=config['dbname']+'-'+str(thisRow[0])+'-'+str(imageCount)+"-"+filename
                blobFile=open(config['mediaPath']+cookieID+'/'+blobName,"wb")
                blobFile.write(thisRow[thisCol])
                blobFile.close()
    
    #                binaryLink=strict401gen.Href("tmp/"+cookieID+'/'+binaryname,text,onClick="window.open(this.href);return false;")
                blobLink=strict401gen.Href("tmp/"+cookieID+'/'+blobName,strict401gen.Image("images/fileTypes/"+iconName,title=blobToolTip,alt=iconName,Class="mediacolimage"),onClick="window.open(this.href);return false;")
                mediaRow.append(strict401gen.TD(blobLink,colspan="1",Class="mediacolimage"))
    
            elif isText:
    
                # it's a text field
                if thisRow[thisCol]==None:
                    value=""
                else:
                    value=thisRow[thisCol]
    
                text1=str(value)
                text2=text1.replace('\r\n','<BR>')
                text3=text2.replace('\n','<BR>')
                text=text3.replace('\r','<BR>')
                    
                if owner:  # special concern for the 'read' db
                    if thisCol==1:
                        text=owner.capitalize()+' writes:<BR><BR>'+text
                        
                if rowHasBinaryData=='yes':
                    mediaRow.append(strict401gen.TD(strict401gen.RawText(text),colspan="1",Class="mediacolnote"))
                else:
                    mediaRow.append(strict401gen.TD(strict401gen.RawText(text),colspan="2",Class="mediacolnote"))
            
            else:
                charRow=strict401gen.TR(Class=row+'row')
                if thisRow[thisCol]:
                
                    # just a char field
                    if fieldNames[thisCol].lower() in config['supportTables']:
                        titleData=getToolTip(fieldNames[thisCol].lower(),thisRow[thisCol],config)                     
                        charRow.append(strict401gen.TD(thisRow[thisCol],title=titleData,Class='supporttooltip'))
                    else:
                        charRow.append(strict401gen.TD(thisRow[thisCol],Class="resultcol"))
                    
                    charTable.append(charRow)
                else:
                    charRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),Class="resultcol"))
                        
                                
        # add the row to the table
        mediaTable.append(mediaRow)

        # add a row to make sure the scroll will go beyond the bottom
        mediaRow=strict401gen.TR()
        mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan=str(len(thisRow))))

    # add row to main table
    if mediaData:
        mediaTable.append(mediaRow)
    else:
        mediaRow=strict401gen.TR()
        mediaRow.append(strict401gen.TD(strict401gen.RawText("No Media Available"),colspan="4"))
        mediaTable.append(mediaRow)
        
    return (mediaTable,str(test))

def createMedia(mediaID,catID,item,config):

    cols=[]
    if mediaID[0]=='I':
        mediaID=mediaID[1:]
        mediaType='Imedia'
    else:
        mediaType='media'

    q="show columns from `"+config['mediaTable']+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in allCols:
        if thisCol[0] in config['primaries']:
            pass
        elif 'timestamp' in thisCol[1]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        elif config['invisible'] in thisCol[0]:
            pass
        else:
            cols.append(thisCol)

    mediaTable=strict401gen.TableLite(Class="edittable edittablecolor")

    count=0
    mediaRow=strict401gen.TR()

    for thisField in cols:
        try:
            fieldlen=thisField[1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

        count=count+1

        if 'enum(' in thisField[1]:
            enumList=thisField[1].split("','")
            enumList[0]=enumList[0][6:]
            enumList[len(enumList)-1]=enumList[len(enumList)-1][:-2]
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(enumList,name=thisField[0],id=thisField[0],Class="editfield")))

        elif 'set(' in thisField[1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],id=thisField[0],multiple=1,size=len(setList),Class="editfield")))

        elif 'text' in thisField[1]:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Textarea(name=thisField[0],id=thisField[0],Class="editfield dataInput")))

        elif 'blob' in thisField[1]:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type='file',name=thisField[0],id=thisField[0],size="10",Class="editfield")))

        elif 'date' in thisField[1]:
            x=str(datetime.date.today()).strip()
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=thisField[0],id=thisField[0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in thisField[1]:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],id=thisField[0],maxlength="6",Class="editfield dataInput")))

        elif 'float' in thisField[1]:
            maxlen=maxlen.split(',')[0]
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],id=thisField[0],maxlength="6",Class="editfield dataInput")))

        elif thisField[0] in config['supportTables']:
            #we have a support table, used to generate a selecet field
            shortList,longList=getPickList(thisField[0],config)
#             test=str(cols[thisField][0])+"  short: "+str(shortList)+"   long: "+str(longList)
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(shortList,name=thisField[0],id=thisField[0],Class="editfield")))            

        else:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],id=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            mediaTable.append(mediaRow)
            mediaRow=strict401gen.TR()
        elif count==len(cols):
            mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
            mediaTable.append(mediaRow)

    if mediaType=='Imedia':
        # find the related item record
        q="select `"+"`,`".join(config['itemListColumns'])+"` from `"+config['itemTable']+\
        "` where `"+config['itemIDfield']+"`='"+str(item[1])+"'"

        info=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
#         caption=str(q)
        caption='Insert '+config['mediaTable']+' for '+" ".join(info)+' '
    else:
        # for a category header
        q2='select `'+config['catInfoColumn']+'` from `'+\
        config['catTable']+'` where `'+ config['catIDfield']+'`="'+str(catID)+'"'

        info=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
        #~ caption='Insert '+config['mediaTable']+' for '+info[0]
        caption='Insert '+config['mediaTable']+' for '+" ".join(info)+' '

    header=formbuttons('create')

    return (caption,header,mediaTable,mediaType)

def editMedia(mediaID,catID,item,config):

    cols=[]
    test=''
    filename=''
    colNames=[]
    if mediaID[0]=='I':
        mediaID=mediaID[1:]
        mediaType='Imedia'
    else:
        mediaType='media'

    # get the column  names
    q="show columns from `"+config['mediaTable']+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in allCols:
        if thisCol[0] in config['primaries']:
            pass
        elif 'timestamp' in thisCol[1]:
            pass
        elif config['owner'] in thisCol[0]:
            pass
        elif config['invisible'] in thisCol[0]:
            q="select `"+thisCol[0]+"` from `"+config['mediaTable']+\
            "` where `"+config['mediaIDfield']+"`='"+mediaID+"'"
            result=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
            if result[0]:
                filename="<br><b> [ "+str(result[0])+" ]</b>"
            else:
                filename=""
        else:
            cols.append(thisCol)
            colNames.append(thisCol[0])

    # get col values
    selectCols=string.join(colNames,"`,`")
    q="select `"+selectCols+"` from `"+config['mediaTable']+\
    "` where `"+config['mediaIDfield']+"`='"+mediaID+"'"

    values=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    mediaTable=strict401gen.TableLite(border="0",Class="edittable edittablecolor")

    count=0
    mediaRow=strict401gen.TR()

    for thisField in range(0,len(cols)):
        try:
            fieldlen=cols[thisField][1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

        count=count+1

        if 'enum(' in cols[thisField][1]:
            enumList=cols[thisField][1].split("','")
            enumList[0]=enumList[0][6:]
            enumList[len(enumList)-1]=enumList[len(enumList)-1][:-2]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))

        elif 'set(' in cols[thisField][1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(setList,name=cols[thisField][0],id=thisField[0],multiple=1,size=len(setList),Class="editfield")))

        elif 'text' in cols[thisField][1]:
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Textarea(values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],rows='10',cols='60',Class="editfield dataInput")))

        elif 'blob' in cols[thisField][1]:
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],id=cols[thisField][0],rlabel=filename,Class="editfield",size="30"),Class="editfield"))

        elif 'date' in cols[thisField][1]:
            if not values[0][thisField] or values[0][thisField]=="None":
                x=string.strip(str(datetime.date.today()))
            else:
                x=values[0][thisField]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=cols[thisField][0],id=cols[thisField][0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in cols[thisField][1]:
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        elif 'float' in cols[thisField][1]:
            maxlen=maxlen.split(',')[0]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        elif cols[thisField][0] in config['supportTables']:
            #we have a support table, used to generate a selecet field
            shortList,longList=getPickList(cols[thisField][0],config)
#             test=str(cols[thisField][0])+"  short: "+str(shortList)+"   long: "+str(longList)
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            if not values[0][thisField] or values[0][thisField]=="None":
                mediaRow.append(strict401gen.TD(strict401gen.Select(shortList,name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))            
            else:
                mediaRow.append(strict401gen.TD(strict401gen.Select(shortList,selected=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],Class="editfield")))            
                
        else: # char fields
            if cols[thisField][0] in config['invisible']:
                mediaRow.append(strict401gen.TD("",Class="editlabel"))
                mediaRow.append(strict401gen.TD(values[0][thisField],Class="editlabel"))               
            else:
                mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
                mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            mediaTable.append(mediaRow)
            mediaRow=strict401gen.TR()
        elif count==len(cols):
            mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
            mediaTable.append(mediaRow)

    if mediaType=='Imedia':
        # find the related item record
        q="select `"+"`,`".join(config['itemListColumns'])+"` from `"+config['itemTable']+\
        "` where `"+config['itemIDfield']+"`='"+str(item[1])+"'"

        info=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        caption='Update '+config['mediaTable']+' for '+" ".join(info)+' '
    else:
        # find the related cat record
        q="select `"+config['catIDfield']+"` from `"+config['mediaTable']+\
        "` where `"+config['mediaIDfield']+"`='"+mediaID+"'"

        value=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        catID=value[0]

        # for a category header
        q2='select `'+config['catInfoColumn']+'` from `'+\
        config['catTable']+'` where `'+ config['catIDfield']+'`="'+str(catID)+'"'

        info=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
        caption='Update '+config['mediaTable']+' for "'+info[0]+'"'

    header=formbuttons('update')

    return(caption,header,mediaTable,mediaType,catID,test)

############ suport Table functions

def supportTable(supportTableName,config):

    test=''
    endWidth="20"

    colWidths,colInfo=getSupportColWidths(supportTableName,config)
    
    if supportTableName=="_config":
        # get all records for this table
        q='select `_id`,`dbname` from '+supportTableName+"`"
        result=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
        
        colwidth="100%"   
    else:
        # get all records for this table
        selected=''
        for thisCol in colInfo:
            # dont' display the filename field 
            if 'filename' not in thisCol[0]:
                col='`'+supportTableName+'`.`'+thisCol[0]+'`,'
                selected=selected+col
            
        q4='select '+selected[:-1]+ ' from `'+supportTableName+"`"
        supportresult=db.dbConnect(config['selectedHost'],config['dbname'],q4,0)
        result=sorted(supportresult, key=itemgetter(1))   # sort by col 1 
        colwidth=""
        
    supportTable=strict401gen.TableLite(CLASS='resultstable')

    # get a list of the fieltypes so I can branch on blob fields
    fieldNames=[]
    fieldTypes=[]
    q="show columns from `"+supportTableName+"`"
    cols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in cols:
        fieldNames.append(thisCol[0])
        fieldTypes.append(thisCol[1])

    try:
        result[0]  # fail text for empty table

        row='odd'

        for thisRecord in result:

            if row=='odd':
                row='even'
            else:
                row='odd'

            supportRow=strict401gen.TR(Class=row+'row')
            recNum=''
            rowHasBinaryData='yes'

            for thisCol in range(0,len(thisRecord)):
                if 'blob' in fieldTypes[thisCol]:
                    try:
                        x=len(thisRecord[thisCol])
                    except:
                        rowHasBinaryData='no'

            editImg="images/edit.png"
            editToolTip="Edit Record"            
            deleteImg="images/delete.png"
            delToolTip="Delete Record"
            if config['login']=='':
                editImg="images/edit-inactive.png"
                editToolTip="Not logged in"
                deleteImg="images/delete-inactive.png"
                delToolTip="Not logged in"                


            for thisCol in range(0,len(thisRecord)):

                # if this col is an image set the image type
                try:
                    isImg="."+imghdr.what('',thisRecord[thisCol])
                    if isImg not in (".png",".jpeg",".gif",".bmp"):
                        isImg=''
                    if isImg=='.jpeg':
                        isImg='.jpg'
                except:
                    isImg=''

                if thisCol==0:
                    recNum=str(thisRecord[thisCol])

                    toolTable=strict401gen.TableLite(CLASS='')
                    toolRow=strict401gen.TR(Class=row+'row')
                    # column for the edit button
                    editImage=strict401gen.Image((editImg,"16","16"),alt="Edit",id="Edit",title=editToolTip)
                    if 'inactive'in editImg:
                        toolRow.append(strict401gen.TD(editImage))
                    else:
                        toolRow.append(strict401gen.TD(strict401gen.Href("index?supportedit="+supportTableName+"&amp;supportID="+str(thisRecord[thisCol]),editImage),colspan="1",Class=""))
                        
                    toolTable.append(toolRow)
                    toolRow=strict401gen.TR(Class=row+'row')

                    # column for the delete link
                    delimage=strict401gen.Image((deleteImg,str(endWidth),str(endWidth)),alt="Del",id="Del",title=delToolTip)
                    if 'inactive' in deleteImg:
                        toolRow.append(strict401gen.TD(delimage,colspan="1",Class="toolcol0"))
                    else:
                        toolRow.append(strict401gen.TD(strict401gen.Href("index?popup=94&amp;supportTableName="+supportTableName+"&amp;supportID="+str(thisRecord[thisCol]),delimage),colspan="1",Class="toolcol0"))
                    toolTable.append(toolRow)
                    supportRow.append(strict401gen.TD(toolTable,colspan="1",Class="toolcol0"))

                elif isImg:
                    # if it's an image write it to disk so the program can load it
                    dir=config['catImagePath']+config['dbname']
                    if os.path.exists(dir):
                        for f in os.listdir(dir):
                            if str(thisRecord[1])+"." in f:
                                os.remove(dir+"/"+f)
                        
                    # imagename must be unique
                    imagename=config['catImagePath']+config['dbname']+'/'+str(thisRecord[1])+isImg
                    imgFile=open(imagename,"wb")
                    imgFile.write(thisRecord[thisCol])
                    imgFile.close()
                    
                    linkPath='catimages/'+config['dbname']+'/'+str(thisRecord[1])+isImg
                    imageLink=strict401gen.Href(linkPath,strict401gen.Image(linkPath,title="Click to view full size image",alt="This is a "+isImg+" file.",Class="mediacolimage"),onClick="window.open(this.href);return false;")
                    supportRow.append(strict401gen.TD(imageLink,colspan="1",Class='mediacolimage'))
                    
                elif thisRecord[thisCol]:
                    colwidth=str(colWidths[thisCol-1])+"px"
                    supportRow.append(strict401gen.TD(thisRecord[thisCol],style="width:"+colwidth,Class="resultcol"))
                else:
                    supportRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),style="width:"+colwidth,Class="resultcol"))

            supportTable.append(supportRow)

#         # last row first col ???? doesn't look like this is needed, it's an attempt to pad the
#         # bottom of the table to make sure I can scroll past the last row.
#         #         supportTable.append(supportRow) supportRow=strict401gen.TR()
#         supportRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="Edit")))
#         # last row middle cols
#         for thisCol in colWidths:
#             supportRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",str(int(thisCol)-2),"10"),alt="Edit")))
#         # last row last col
#         supportRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="Edit")))
#         supportTable.append(supportRow)

    except:
        row='odd'

        supportRow=strict401gen.TR(Class=row+'row')
        supportRow.append(strict401gen.TD(strict401gen.RawText("No records found for "+supportTableName),colspan="1"))
#         supportRow.append(strict401gen.TD(imagename,colspan="1"))
        supportTable.append(supportRow)
    
    header=[]
    caption=''
    if supportTableName=="_config":
        header.append('Name of Database')
    else:
        for thisCol in colInfo:
            if '_' not in thisCol[0] and 'filename' not in thisCol[0]:
                header.append(thisCol[0])


    return (supportTable,colWidths,header,test)

def editSupport(supportTableName,supportID,config):

    cols=[]
    test=''
    filename=''
    colNames=[]

    # get the column  names
    q="show columns from `"+supportTableName+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    for thisCol in allCols:
        if 'PRI' in thisCol[3]:
            supportIDfield=thisCol[0]
#             pass
        elif config['invisible'] in thisCol[0]:
            q4="select `"+supportTableName+'`.`'+thisCol[0]+"` from `"+supportTableName+\
            "` where `"+supportIDfield+"`='"+supportID+"'"
            result4=db.dbConnect(config['selectedHost'],config['dbname'],q4,1)
            try:
                result4[0]
                filename="<br><b> [ "+str(result4[0])+" ]</b>"
            except:
                filename="no"
        else:
            cols.append(thisCol)
            colNames.append(thisCol[0])

    # get col values
    selectCols=string.join(colNames,"`,`")
    q="select `"+selectCols+"` from `"+supportTableName+\
    "` where `"+supportIDfield+"`='"+supportID+"'"

    values=db.dbConnect(config['selectedHost'],config['dbname'],q,1)

    supportTable=strict401gen.TableLite(border="0",Class="edittable edittablecolor")

    count=0    
    
    if supportTableName=="_config":
        supportComment=strict401gen.TR(Class='oddrow')
        supportRow=strict401gen.TR(Class='evenrow')
    else:
        supportRow=strict401gen.TR()

    for thisField in range(0,len(cols)):
        try:
            fieldlen=cols[thisField][1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''

            
        if supportTableName=="_config":
            # only for the config table
            imageList=getImageList(config)
            themeList=getThemeList(config)
            sizelen='70'
            try:
                q="show full columns from `"+supportTableName+"` where `Field`='"+cols[thisField][0]+"'"
                row=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
                comment=row[-1]
            except:
                comment='no comment'
                
            supportComment.append(strict401gen.TD(str(comment),Class="editlabel",colspan=str(len(cols))))
            supportRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel",style="font-weight:bold"))
#             selectedValues=values[thisField]
#             if selectedValues==None:
            try:
                selectedValues=values[thisField]
            except:
                selectedValues=""
                
            if "enum" in cols[thisField][1]:
                    enumList=cols[thisField][1][6:-2].split("','")
                    supportRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
            else:
                if 'item' in cols[thisField][0].lower():
                    if 'table'in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['tableNames'],selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'columns' in cols[thisField][0].lower():
                        if len(selectedValues)>1:
                            selectedValues=selectedValues.split()
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['itemShowColumns'],multiple=1,size=5,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'cat' in cols[thisField][0].lower():
                    if 'table' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['tableNames'],selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'columns' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['catShowColumns'],multiple=1,size=5,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'column' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['catShowColumns'],selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'media' in cols[thisField][0].lower():
                    if 'table' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['tableNames'],selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'columns' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['mediaShowColumns'],multiple=1,size=5,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'column' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['mediaShowColumns'],selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'logo' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(imageList,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'background' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(imageList,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))                    
                elif 'theme' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(themeList,selected=selectedValues,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))                    
                else:
                        supportRow.append(strict401gen.TD(strict401gen.Input(type="text",value=selectedValues,name=cols[thisField][0],id=cols[thisField][0],size=sizelen,maxlength=maxlen,Class="editfield dataInput")))
#                         supportRow.append(strict401gen.TD(strict401gen.Input(type="text",value=str(cols[thisField]),id=cols[thisField][0],size=sizelen,maxlength=maxlen,Class="editfield dataInput")))
#                         supportRow.append(strict401gen.TD(strict401gen.Input(type="text",value='test',id=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))
            
        else:
            # for all other support tables    
            count=count+1
        
            if 'blob' in cols[thisField][1]:
                supportRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
                supportRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],id=cols[thisField][0],rlabel=filename,Class="editfield",size="30"),Class="editfield"))
                
            else:
                if cols[thisField][0] in config['invisible']:
                    supportRow.append(strict401gen.TD("",Class="editlabel"))
                    supportRow.append(strict401gen.TD(values[thisField],Class="editlabel"))               
                else:
                    supportRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
                    supportRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[thisField],name=cols[thisField][0],id=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))


        if supportTableName=="_config":
                supportComment=strict401gen.TR(Class='oddrow')
                supportRow=strict401gen.TR(Class='evenrow')
                supportTable.append(supportComment)
                supportTable.append(supportRow)
            
        else:
            if not count%2:
                supportTable.append(supportRow)
                supportRow=strict401gen.TR()
            elif count==len(cols):
                supportRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
                supportTable.append(supportRow)

    caption='Update '+supportTableName
        
    header=formbuttons('update')

    return(caption,header,supportTable,'support')

def createSupport(supportTableName,config):


    cols=[]
    colNames=[]
    
    q="show columns from `"+supportTableName+"`"
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    for thisCol in allCols:
        if 'PRI' in thisCol[3]:
#             supportIDfield=thisCol[0]
            pass
        elif config['invisible'] in thisCol[0]:
            pass
        else:
            cols.append(thisCol)
            colNames.append(thisCol[0])

    supportTable=strict401gen.TableLite(border="0",Class="edittable edittablecolor")

    count=0
    
    
    if supportTableName=="_config":
        imageList=getImageList(config)
        themeList=getThemeList(config)
        supportComment=strict401gen.TR(Class='oddrow')
        supportRow=strict401gen.TR(Class='evenrow')
    else:
        supportRow=strict401gen.TR()
        
    for thisField in range(0,len(cols)):

        try:
            fieldlen=cols[thisField][1]
            maxlen=fieldlen[fieldlen.index("(")+1:fieldlen.index(")")]
        except:
            maxlen=''
            
        if supportTableName=="_config":
            sizelen='70'
            try:
                q="show full columns from `"+supportTableName+"` where `Field`='"+cols[thisField][0]+"'"
                comment=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
            except:
                comment='no comment'
            supportComment.append(strict401gen.TD(str(comment[-1]),Class="editlabel",colspan=str(len(cols))))
            supportRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel",style="font-weight:bold"))
#             supportRow.append(strict401gen.TD(strict401gen.Input(type="text",id=cols[thisField][0],size=sizelen,maxlength=maxlen,Class="editfield dataInput")))
            
            if "enum" in cols[thisField][1]:
                    enumList=cols[thisField][1][6:-2].split("','")
                    supportRow.append(strict401gen.TD(strict401gen.Select(enumList,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
            else:
                if 'item' in cols[thisField][0].lower():
                    if 'table'in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['tableNames'],name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'columns' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['itemShowColumns'],multiple=1,size=5,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'cat' in cols[thisField][0].lower():
                    if 'table' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['tableNames'],name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'columns' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['catShowColumns'],multiple=1,size=5,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'column' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['catShowColumns'],name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'media' in cols[thisField][0].lower():
                    if 'table' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['tableNames'],name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'columns' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['mediaShowColumns'],multiple=1,size=5,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                    elif 'column' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(config['mediaShowColumns'],name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'logo' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(imageList,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))
                elif 'background' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(imageList,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))                    
                elif 'theme' in cols[thisField][0].lower():
                        supportRow.append(strict401gen.TD(strict401gen.Select(themeList,name=cols[thisField][0],id=cols[thisField][0],style='width:80%',Class="editfield")))                    
                else:
                    try:
                        defaultValue=config[cols[thisField][0]]
                    except:
                        defaultValue=''
                    supportRow.append(strict401gen.TD(strict401gen.Input(type="text",name=cols[thisField][0],id=cols[thisField][0],value=defaultValue,size=sizelen,maxlength=maxlen,Class="editfield dataInput")))
            
        else:    
            count=count+1
    
            if 'blob' in cols[thisField][1]:
                supportRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
                supportRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],id=cols[thisField][0],size="10",Class="editfield")))

            else:
                supportRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
                supportRow.append(strict401gen.TD(strict401gen.Input(type="text",name=cols[thisField][0],id=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))

        if supportTableName=="_config":
                supportComment=strict401gen.TR(Class='oddrow')
                supportRow=strict401gen.TR(Class='evenrow')
                supportTable.append(supportComment)
                supportTable.append(supportRow)
            
        else:
            if not count%2:
                supportTable.append(supportRow)
                supportRow=strict401gen.TR()
            elif count==len(cols):
                supportRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2"))
                supportTable.append(supportRow)

    caption='Insert into '+supportTableName

    header=formbuttons('create')

    return(caption,header,supportTable,'support')

def supportForm(supportTableName,config):
    
    tables=config['supportTables']
    tables.insert(0,"Support Tables")
    supportList=strict401gen.Select(config['supportTables'],onChange="javascript:document.newSupport.submit();",size=1,name='supportTableName',id='supportTableName',Class="topfield")
    form=strict401gen.Form(submit="",name='newSupport',id='newSupport',cgi='index?action=23')
    form.append(supportList)
#     form.append(strict401gen.Input(type='hidden',name='supportTableName',id='supportTableName',value=supportTableName))
    
    return(form)

############ misc functions

def relatedRecords(itemID,config):

    # see if there is at least one record in the cat table related to the current item
    # return a 1 if there is, a zero if not
    records=[]
    q="SELECT * FROM `"+config['catTable']+"` where `"+config['catTable']+"`.`"+config['itemIDfield']+"`='"+str(itemID)+"'"
    r=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
    if r:
        records.append(r)
    related=str(len(records))

    return related

def cleanTmp(config):

    # delete the tmp files whenever itemQuery or catQuery are called

    subDirs=os.listdir(config['mediaPath'])
    for thisItem in subDirs:
        if thisItem[0]!=".":
            if os.path.isdir(config['mediaPath']+thisItem):
                shutil.rmtree(config['mediaPath']+thisItem)
            elif os.path.isfile(config['mediaPath']+thisItem):
                os.remove(config['mediaPath']+thisItem)
    return

def lastUpdate(config):

    q='select `'+\
    config['mediaTable']+'`.`'+config['catIDfield']+'`,`'+\
    config['mediaTable']+'`.`modstamp`'+\
    ' from `'+config['mediaTable']+\
    '` order by `'+config['mediaTable']+'`.`modstamp`'+' desc'

    qresult1=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    record=0
    while not qresult1[record][0]:
        record=record+1
    else:
        catID=str(qresult1[record][0])

    q2="select `"+\
    config['catTable']+'`.`'+config['itemIDfield']+\
    '` from `'+config['catTable']+\
    '` where `'+config['catTable']+'`.`'+config['catIDfield']+'`="'+catID+'"'

    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
    itemID= str(qresult[0])

    return (itemID,catID)

def formbuttons(which):

    if which=='update':
        saveButton=strict401gen.Input(type="image",name='updatebutton',id="updatebutton",srcImage="images/UPDATE.png",alt="UPDATE",title="Update this Record")
        cancelButton=strict401gen.Input(type="image",name='cancelbutton',id="cancelbutton",srcImage="images/CANCEL.png",alt="CANCEL",title="Cancel Edit")

    elif which=='create':
        saveButton=strict401gen.Input(type="image",name='savebutton',id="savebutton",srcImage="images/SAVE.png",alt="SAVE",title="Save this Record")
        cancelButton=strict401gen.Input(type="image",name='cancelbutton',id="cancelbutton",srcImage="images/CANCEL.png",alt="CANCEL",title="Cancel Edit")

    elif which=='item':
        saveButton=strict401gen.Input(type="image",name='savebutton',id="savebutton",srcImage="images/notes.png",alt="SAVE",title="Save this Record")
        cancelButton=strict401gen.Input(type="image",name='cancelbutton',id="cancelbutton",srcImage="images/edit3.png",alt="CANCEL",title="Cancel Edit")

    return [saveButton,cancelButton]

def getCatColWidths(header, config):

    colLengths=[]
    minColLen=7
    maxColLen=18
    dateLen=10
    tableWidth=720

    # column lengths for the item table
    q="show columns from `"+config['itemTable']+"`"
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    # special case, combo item/cat header
    if header[0]==config['itemTable'].upper():
        colLen=0
        for thisCol in colInfo:
            if thisCol[0] in config['itemListColumns']:
                colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
                colLen=colLen+int(colLength)
        if colLen<minColLen:
            colLen=minColLen
        if colLen>maxColLen:
            colLen=maxColLen

        colLengths.append(colLen)

    # column lengths for the catTable
    q="show columns from `"+config['catTable']+"`"
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    for headerCol in header:
        colLen=0

        for thisCol in colInfo:

            if thisCol[0].upper() == headerCol:

                if 'date' in thisCol[1]:
                    colLen=dateLen

                elif 'enum' in thisCol[1]:
                    enumLen=0
                    enumerations=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")].split("'")
                    for thisEnum in enumerations:
                        if len(thisEnum)>enumLen:
                            enumLen=len(thisEnum)
                    colLen=enumLen
                    if colLen<minColLen:
                        colLen=minColLen
                    if colLen>maxColLen:
                        colLen=maxColLen

                elif thisCol[0] not in config['primaries']:
                    try:
                        colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
                        if "," in colLength:
                            colLen=int(colLength.split(",")[0])
                            if colLen<minColLen:
                                colLen=minColLen
                            if colLen>maxColLen:
                                colLen=maxColLen
                        else:
                            colLen=int(colLength)
                            if colLen<minColLen:
                                colLen=minColLen
                            if colLen>maxColLen:
                                colLen=maxColLen
                    except:
                        pass

        if colLen:
            colLengths.append(colLen)


    # total up all col lens
    colTotalLen=0
    for colLen in colLengths:
            colTotalLen=colTotalLen+colLen

    # convert lens to width in pix based on a table width set above
    colWidths=[]
    colLens=[]
    for thisCol in range(0,len(colLengths)):
        a=float(colLengths[thisCol])
        b=float(a/colTotalLen)
        c=int(b*tableWidth)
        colWidths.append(str(c))
        colLens.append(str(colLengths[thisCol]))

    return colWidths

def getItemColWidths(header,config):

    colLengths=[]
    minColLen=10
    maxColLen=25
    dateLen=10
    tableWidth=725

    # column lengths for the item table
    q="show columns from `"+config['itemTable']+"`"
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)


    # special case search, combo item/cat header
    if header[0]==config['itemTable'].upper():
        colLen=0
        for thisCol in colInfo:
            if thisCol[0] in config['itemListColumns']:
                colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
                colLen=colLen+int(colLength)
        if colLen<minColLen:
            colLen=minColLen
        if colLen>maxColLen:
            colLen=maxColLen

        colLengths.append(colLen)

    else:

        for headerCol in header:
            colLen=""

            for thisCol in colInfo:

                if thisCol[0].upper() == headerCol:

                    if 'date' in thisCol[1]:
                        colLen=dateLen

                    elif 'enum' in thisCol[1]:
                        enumLen=0
                        enumerations=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")].split("'")
                        for thisEnum in enumerations:
                            if len(thisEnum)>enumLen:
                                enumLen=len(thisEnum)
                        colLen=enumLen
                        if colLen<minColLen:
                            colLen=minColLen
                        if colLen>maxColLen:
                            colLen=maxColLen

                    elif thisCol[0] not in config['primaries']:
                        try:
                            colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
                            if "," in colLength:
                                colLen=int(colLength.split(",")[0])
                                if colLen<minColLen:
                                    colLen=minColLen
                                if colLen>maxColLen:
                                    colLen=maxColLen
                            else:
                                colLen=(int(colLength))
                                if colLen<minColLen:
                                    colLen=minColLen
                                if colLen>maxColLen:
                                    colLen=maxColLen
                        except:
                            pass

            if colLen:
                colLengths.append(colLen)

    # total up all col lens
    colTotalLen=0
    for colLen in colLengths:
            colTotalLen=colTotalLen+colLen

    # convert lens to width in pix based on a table width set above
    colWidths=[]
    colLens=[]
    for thisCol in range(0,len(colLengths)):
        a=float(colLengths[thisCol])
        b=float(a/colTotalLen)
        c=int(b*tableWidth)
        colWidths.append(str(c))
        colLens.append(str(colLengths[thisCol]))

    return colWidths

def getMediaColWidths(req,config):

    colLengths=[]
    tableWidth=725
    minColLen=5
    maxColLen=int(tableWidth/2)
    dateLen=10
    startImageWidth=32
    endImageWidth=128

    # column lengths for the item table
    q="show columns from `"+config['mediaTable']+"`"
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)


    for thisCol in colInfo:
        colLen=0

        if 'date' in thisCol[1]:
            colLen=dateLen

        elif 'enum' in thisCol[1]:
            enumLen=0
            enumerations=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")].split("'")
            for thisEnum in enumerations:
                if len(thisEnum)>enumLen:
                    enumLen=len(thisEnum)
            colLen=enumLen
            if colLen<minColLen:
                colLen=minColLen
            if colLen>maxColLen:
                colLen=maxColLen

        elif 'text' in thisCol[1]:
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(thisCol)+"---"+repr(colLen))
            colLen=maxColLen

        elif thisCol[0] not in config['primaries']:
            try:
                colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
                if "," in colLength:
                    colLen=int(colLength.split(",")[0])
                    if colLen<minColLen:
                        colLen=minColLen
                    if colLen>maxColLen:
                        colLen=maxColLen
                else:
                    colLen=(int(colLength))
                    if colLen<minColLen:
                        colLen=minColLen
                    if colLen>maxColLen:
                        colLen=maxColLen
            except:
                pass

        #~ else:
            #~ pass


        if colLen:
            colLengths.append(colLen)

    #~ util.redirect(req,"testValue.py/testvalue?test="+repr(colLengths)+"---"+repr(colInfo))

    # total up all col lens
    colTotalLen=0
    for colLen in colLengths:
            colTotalLen=colTotalLen+colLen

    # convert lens to width in pix based on a table width set above
    colWidths=[]
    colLens=[]
    for thisCol in range(0,len(colLengths)):
        a=float(colLengths[thisCol])
        b=float(a/colTotalLen)
        c=int(b*(tableWidth-(startImageWidth+endImageWidth)))
        colWidths.append(str(c))
        colLens.append(str(colLengths[thisCol]))

    return colWidths

def getSupportColWidths(tableName,config):
    
    tableWidth=740

    # column lengths for the item table
    q="show columns from `"+tableName+"`"
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    totalColLength=0
    colLengths=[]
    colPercents=[]
    for thisCol in colInfo:
        # Support tables only support char type cols
        if 'char' in thisCol[1]:
            colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
            colLen=int(colLength)
            colLengths.append(colLen)
            totalColLength=totalColLength+int(colLen)
            
    for thisCol in colLengths:
        colPercents.append(thisCol*100/totalColLength)
            
    colWidths=[]            
    for thisPercent in colPercents:
        colWidths.append(tableWidth*thisPercent/100)
    
    return (colWidths,colInfo)

def updateCookie(req,name,value,config):

    data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])
    data[name]=value
    kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])

    return



############ about functions

def aboutInfo(config):

    caption="About 3t"
    header=""
    result=[\
    ["Author: Gary M Witscher"],
    ["Date: 2014-07-07"],
    ["Version: 2.4"],
    ["License: Free (as in beer and chicken)"],
    ["W3C Markup Validation: HTML 4.01 Strict"],
    ["W3C CSS Validation: CSS2"],
    ["- How Did This All Come About and Why"],
    ["Some time back I wrote a web based MySQL client to handle the task "\
    "of keeping track of my numerous automobile repairs. I was hoping to "\
    "avoid repeating my automotive mistakes and to track expenses. It all worked out "\
    "fairly well, but the client interface was not as simple as it needed to be. "\
    "This was due to the fact that as I developed it I expanded my needs and found that "\
    "it needed to handle any and all data bases and data types. This sort of completeness "\
    "produced UI complexities that didn't allow fast and easy data access. "\
    "So, I set about to build a UI that would be simple to use. This is version 2 in that series."],
    ["- A Little About the Layout"],
    ["This Web App is specifically designed to display, edit, and search  three related tables. "\
    "The primary table is the 'itemTable'. Data linked to each Item is stored "\
    "in the secondary table (catagory table, or 'catTable'). The 'itemTable' has an image "\
    "field for storing an image of that item. The 'catTable' has a links to a 'mediaTable' "\
    "for storing notes and related images about the specific record. There is also a kooky "\
    "table that is designed to allow for multiple logins."],
    ["- MySQL Information"],
    ["All the data is stored in a MySQL data base. Information on how to configure the "\
    "data base can be found in the INSTALL file in the main directory. This version will only "\
    "handle three tables, very specific tables. I call the first one 'Auto' (the itemTable), the second one "\
    " is 'Service' (the catTable). The third one is a media table called 'note'. "
    "If you want the features I've programmed into this script you will "\
    " have to abide by the strict table definitions I've provided. Although you can name them and their "\
    "fields anything you want. And they can contain any data you like. This is not JUST an Auto DB, "\
    "I've used it for a 'Books I've Read DB' and have plans to use it for many other dbs."],
    ["- Requirements"],
    ["The app must run under Apache ver2 or later unless you want to make some major code changes."\
    "It uses Python2.5 and ModPython and MySQL-python. In addition it uses enumeration fields, which "\
    "as far as I know are not found outside of MySQL. So, I think your stuck with MySQL."]
    ]

    return (caption,header,result,'item')

def aboutTable(aboutData,config):

    resultTable=strict401gen.TableLite(CLASS='')
    row='odd'
    aboutIntro="font:10pt Tahoma, serif;text-align:center;"

    for thisRow in aboutData:
        # indicates a title line
        if thisRow[0][0]=="-":

            if row=='odd':
                row='even'
            else:
                row='odd'

            rRow=strict401gen.TR(Class=row+'row')
            rRow.append(strict401gen.TD(thisRow[0][1:],style="width:785px;font: 14pt Times, serif, bold;text-align:center;"))
            aboutIntro="font:10pt Arial, sans;text-align:left;"
            
        # not a title, just a data line
        else:
            rRow=strict401gen.TR(Class=row+'row')
            rRow.append(strict401gen.TD(thisRow[0],style="width:785px;"))

        resultTable.append(rRow)

    if row=='odd':
        row='even'
    else:
        row='odd'

    rRow=strict401gen.TR(Class=row+'row')
    rRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),style="width:785px;"))
    resultTable.append(rRow)

    return (resultTable)

def editConfig(req,config):

    configTable=strict401gen.TableLite(Class="edittable edittablecolor")

    maxsize=50
    maxlen=50

    confFile=open(config['configFile'],"rb")
    lines=confFile.readlines()
    confFile.close()

    for thisLine in range(0,len(lines)):
        if 'start of configuration' in lines[thisLine]:
            startConfig=thisLine
            break
        elif lines[thisLine].strip()=='':
            configRow=strict401gen.TR()
            configRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2",Class="editlabel"))
            configTable.append(configRow)
        else:
            configRow=strict401gen.TR()
            configRow.append(strict401gen.TD(lines[thisLine],colspan="2",Class="editlabel"))
            configTable.append(configRow)

    descText=''
    passInput=0
    row='odd'

    for thisLine in range(startConfig,len(lines)):

        if lines[thisLine][0:2]=="# ":
            pass
        elif lines[thisLine].strip()=="#":
            pass
        elif lines[thisLine].strip()=='':
            pass
        elif lines[thisLine][0:2]=="##":

            if lines[thisLine+1][0:2]=="##":
                descText=lines[thisLine][2:]
                passInput=1
            else:
                descText=descText+lines[thisLine][2:]
                configRow=strict401gen.TR()
                configRow.append(strict401gen.TD(descText,colspan="1",Class=row+'row'))
                passInput=0
                descText=""

                if row=='odd':
                    row='even'
                else:
                    row='odd'

        elif "#" not in lines[thisLine] and "=" in lines[thisLine] and passInput==0:
            configData=lines[thisLine].split("=")
            configName=configData[0]
            configValue=configData[1]
            configRow.append(strict401gen.TD(strict401gen.Input(type="text",value=configValue,id=configName,size=maxsize,maxlength=maxlen,Class="editfield dataInput"),colspan="1"))

            configTable.append(configRow)


    caption='Edit configuration.'
    header=formbuttons('update')

    return (caption,header,configTable,'writeConfig')

def createConfig(req,config):

    configTable=strict401gen.TableLite(Class="edittable edittablecolor")

    maxsize=30
    maxlen=50

    confFile=open(config['configFile'],"rb")
    lines=confFile.readlines()
    confFile.close()

    for thisLine in range(0,len(lines)):
        if 'start of configuration' in lines[thisLine]:
            startConfig=thisLine
            break
        elif lines[thisLine].strip()=='':
            configRow=strict401gen.TR()
            configRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="2",Class="editlabel"))
            configTable.append(configRow)
        else:
            configRow=strict401gen.TR()
            configRow.append(strict401gen.TD(lines[thisLine],colspan="2",Class="editlabel"))
            configTable.append(configRow)

    descText=''
    passInput=0
    row='odd'

    for thisLine in range(startConfig,len(lines)):

        if lines[thisLine][0:2]=="# ":
            pass
        elif lines[thisLine].strip()=="#":
            pass
        elif lines[thisLine].strip()=='':
            pass
        elif lines[thisLine][0:2]=="##":

            if lines[thisLine+1][0:2]=="##":
                descText=lines[thisLine][2:]
                passInput=1
            else:
                descText=descText+lines[thisLine][2:]
                configRow=strict401gen.TR()
                configRow.append(strict401gen.TD(descText,colspan="1",Class=row+'row'))
                passInput=0
                descText=""

                if row=='odd':
                    row='even'
                else:
                    row='odd'


        elif "#" not in lines[thisLine] and "=" in lines[thisLine] and passInput==0:
            configData=lines[thisLine].split("=")
            configName=configData[0]
            configValue=''
            configRow.append(strict401gen.TD(strict401gen.Input(type="text",value=configValue,id=configName,size=maxsize,maxlength=maxlen,Class="editfield dataInput"),colspan="1"))

            configTable.append(configRow)


    caption='Create configuration.'
    header=formbuttons('create')

    return (caption,header,configTable,'writeConfig')

def getFileType(fileData):
    error=""
    fileType=""
    # keep pk test to first as odf files are also pk files, matches are case sensitive
    # tiff signatures "II" and "MM" or 0x49 0x49 0x2a 0x00 and 0x4d 0x4d 0x00 0x2a
    # checking a str here, so don't know how to check the hex code for tiff.
    # a significant certainty could be established using hex instead of ascii and by setting a start/stop byte location for each filetype
    fileTypes={
               ("PK",):"zip",               
               ("II*","MM.*"):"tiff",
               ("%PDF",):"pdf",
               ("%!PS",):"ps",
               ("MSWordDoc",):"doc",
               ("RIFF","AVI","LISTR","ftyp","matroska","moov","MPEG"):"video",
               ("opendocument.text","opendocument.spreadsheet"):"odf",
               ("ID3","OggS","WMA"):"audio",
               ("!DOCTYPE","<HTML>","<html>","<BODY>","<body>"):"html",
               }
    # apparently id's can be deeply imbedded, like MSWordDoc could need 240 bytes or more.
    # I branch to this based on a minumum of 128 bytes and I'd like to test less
    # but opendocument needs at least 90, so here I am caught between a rock and a hard spot.
    # this seems to get most files id'd.
    fileSample=fileData[0:128] 
    fileMagic=fileTypes.keys()
    for thisType in fileMagic:
        for thisMagic in thisType:
            if thisMagic in fileSample:
                fileType=fileTypes[thisType]

    if fileType=="":
        fileType="unknown"
        
    return fileType

def getFileType2(fileName):
    
    error=""
    fileExt=fileName.split(".")[-1].lower()
    
    fileType=""
    # assigning files an icon based on file extension
    fileTypes={
               ("zip","tar","gz","tgz"):"archived",               
               ("tiff"):"tiff",
               ("pdf",):"pdf",
               ("ps",):"ps",
               ("doc","docx",'txt'):"doc",
               ("mp4","avi","mkv","mov","flv","wmv"):"video",
               ("odf","odt","ods","odp"):"odf",
               ("mp3","ogg","wma","wav"):"audio",
               ("html","htm","xml"):"web",
               ("py","sh","css","js","conf","cfg","config"):"source",
               }
    
    typeKeys=fileTypes.keys()
    for thisType in typeKeys:
        if fileExt in thisType:
            fileType=fileTypes[thisType]

    if fileType=="":
        fileType="unknown"
        
    return fileType

def getPickList(tableName,config):
    
    # This function returns a pick list used for columns that
    # have a support table by the same name that supplies
    # a selection of values for that column.
    # The category table is one exception to that rule
    # in that the column is supports doesn't need to have
    # the same name, it needs to be setup as the catColumn in the config.
    
    if tableName==config['catColumn']:
        tableName=config['categoryTable']
    
    # get table rows
    q="select * from `"+tableName+"`"
    rows=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    q="show columns from `"+tableName+"`"
    cols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    # make a short list of values to display in the pick list
    # the short list is keyed to fields that end in _ (falling back to the first str field)
    # make a long list of complete info to display on mouse over.
    shortList=[]
    longList=[]
    try:
        for thisRow in rows:
            shortTxt=''
            longTxt=''
            for thisCol in range(0,len(cols)):
                if isinstance(thisRow[thisCol],str):
                    if cols[thisCol][0][-1]=="_":
                        shortTxt=shortTxt+" "+thisRow[thisCol]
                    longTxt=longTxt+" "+str(thisRow[thisCol])
                       
            shortList.append(shortTxt.strip())
            longList.append(longTxt.strip())
    except:
        pass
    
    # no fields ended in _ so just use the first string field as a fallback
    # This will also handle the catColumn list.
    
    if len(''.join(shortList).strip())==0:
        shortList=[]
        for thisRow in rows:
            if isinstance(thisRow[1],str):
                shortList.append(thisRow[1])
            else:
                shortList.append('Empty column')
                    
    if shortList:
        # Remove 'All Records' for catColumn selection
        if 'All Records' in shortList:
            shortList.remove('All Records')
    else:
        shortList.append('Empty List')
    if longList:
        pass
    else:
        longList.append('Empty List')

    shortList.sort()
    longList.sort()
                
    return (shortList,longList)

def getToolTip(colName,colValue,config):
    
    toolTip="Details Unavailable"
    tableName=colName
    
    # get table cols
    q="show columns from `"+tableName+"`"
    cols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
     
    orderedCols=[]
    shortCols=[]
    # extract the '_' fields and insert then at the begining
    # so that the short text value will match 
    for thisCol in cols:
        if thisCol[0][-1]=="_":
            shortCols.insert(0,thisCol[0])
        else:
            if 'PRI' not in thisCol[3]:
                orderedCols.append(thisCol[0])
            
    for thisCol in shortCols:
        orderedCols.insert(0,thisCol)
    
    # use the sorted columns to get the full row values
    selectText=''
    for thisCol in orderedCols:
        selectText=selectText+"`"+thisCol+"`,"
    selectText=selectText[:-1]
    
    q="select "+selectText+" from `"+tableName+"`"
    rows=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    # join the row values into text and look for a short text match
    rowText=[]
    for thisRow in rows:
        # protection against null/none column values
        try:
            rowText.append(" ".join(thisRow))
        except:
            rowText.append("")
            
    for thisText in rowText:
        try:
            if colValue.upper() in thisText.upper():
                toolTip=thisText
                break
        except:
            pass
        
    # for debuging
#     toolTip=str(rowText)
      
            
    return toolTip

def getImageList(config):
    
    # gets a list of images to pick from in the configuration dialog
    dbImagePath=config['dbImagePath']+config['dbname']+'/'
    
    # if the dir exists remove all files
    if os.path.exists(dbImagePath):
        pass
    else:
        # make the dir
        os.mkdir(dbImagePath)
        # copy the default images to the db specific dir, all images found will be copied
        defaultsPath=config['defaultImagePath']+'defaults'
        defaultImages=os.listdir(defaultsPath)
        for image in defaultImages:
            if os.path.isfile(config['defaultsPath']+image):
                shutil.copy('defaultsPath'+image,dbImagePath)
    
    
    # remove all hidden files
    images=[]
    default=''
    fileNames=os.listdir(dbImagePath)
    for thisFile in fileNames:
        if thisFile[0]=='.':
            pass
        elif 'default' in thisFile:
            default=thisFile
        else:
            images.append(thisFile)
            
    if default:
        images.insert(0,default)
    
    return images

def getThemeList(config):
    
    # gets a list of css files to pick from in the configuration dialog
    dbThemePath=config['rootPath']+'/style/'
        
    
    # remove all hidden files
    themes=[]
    default=''
    fileNames=os.listdir(dbThemePath)
    for thisFile in fileNames:
        if thisFile[0]=='.':
            pass
        elif thisFile=='base.css':
            pass
        elif 'default' in thisFile:
            default=thisFile.split('.')[0]
        else:
            themes.append(thisFile.split('.')[0])
            
    if default:
        themes.insert(0,default)
    
    return themes