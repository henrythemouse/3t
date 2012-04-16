import db
import string
import strict401gen
import os
import datetime
import imghdr
import kooky2
import myFunctions
import mimetypes
import shutil


from mod_python import psp,util
from mod_python import apache

'''
$LastChangedDate$
$Rev$
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
    vars={}
    resultImg=""
    itemImage=''
    cancelAction=0
    access=''
    username=''
    userpass=''

    try:
        x=req.form.list
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(x))
    except:
        pass
    
    # if the url has a config name passed I use it to select
    # a specific config file written for the db of the same name. 
    # Hopefully I also supply a default config file that will load
    # a default db in the case where a config name is not passed with the url.
    try:
        configDB=req.form['config'].value
        config=myFunctions.getConfig(req,configDB)
        setDBkooky=kooky2.myCookies(req,"","",configDB,"")
    except:
        # all I want here is the dbname from the browser cookie
        # which gives me the config name to retrieve the configuration
        kookyDB=kooky2.myCookies(req,"db","","","")
        try:
            config=myFunctions.getConfig(req,kookyDB)
        except:
            config=myFunctions.getConfig(req,"")
            
    # column lengths for the item table
    q="show columns from "+config['catTable']
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    # check for a config error 
    try:
        x=config['configError']
    except:
        util.redirect(req,"testValue.py/testvalue?test=CONFIG ERROR: "+repr(config))
                
    if config['configError']=="configError":
        action=100
    else:        
        # write item images to disk for now until I can use them from the db
        writeImgs(config)
        cookieID=kooky2.myCookies(req,'','','','')#['kookyID']
        
        try:
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
        
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(error))
        
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
        try:
            searchMode=req.form['searchMode']
        except:
            searchMode=''
            
        try:                # if available, get the cat record formdata - edit a record
            catID=req.form['edit']
            action=12
        except:
            try:                # if available, get the cat record formdata - edit a record
                catID=req.form['alledit']
                action=12
            except:
                catID=''


        try:                # if available, get the cat record formdata - media display
            mediaID=req.form['media']
            action=15
            if 'new' in mediaID:
                catID=mediaID[3:]
                mediaID=mediaID[0:3]
                action=17
        except:
            try:                # edit the media record
                mediaID=req.form['medit']
                action=16
            except:
                mediaID=''
                
        try:
            popup=req.form['popup'].value
        except:
            popup=''

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
            try:
                req.form['searchbutton.x']
            except:
                searchText=data['searchText']
            if not catID:
                catID=data['catID']
        except:
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(data))
            pass
    

        
    # *******************************************
    # item image and navagation
    if action in (1,2,3,4):       # index item
        
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        currentItem=indexItem(item,itemSelected,action)
        item=itemData(currentItem,config)
        itemSelect=itemForm(item[4],currentItem)
        itemImage=itemImg(itemImage,item,config)
        search=searchForm(searchText)
        results=itemQuery(currentItem,item,config)
        cleanTmp(config)
#        util.redirect(req,"testValue.py/testvalue?test="+repr(results)+repr(currentItem))
        
        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        cancelAction=3
        
        if currentItem==0:
            # this is for ALL items listing
            headerWidths=getItemColWidths(resultHeader,config)
            resultTable=itemAllTable(resultData,"",resultHeader,headerWidths,config)
        else:
            # a single item listing
            resultTable=itemTable(resultData,config)

    # *******************************************
    # category image and navagation
    
    elif action in (5,6,7,8):     # category
        
        itemSelect=itemForm(item[4],currentItem)
        currentCat=indexCat(currentCat,catImages,catSelected,action)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        results=catQuery(req,catImages[currentCat][0],item[1],config)
        cleanTmp(config)
        
        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        cancelAction=7

        headerWidths=getCatColWidths(resultHeader,config)
        resultTable=catTable(resultData,catImages[currentCat][0],resultHeader,headerWidths,config)
        
    elif action==10:     # edit item 
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
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
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=createItem(currentCat,item,config)
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==12:     # edit catagory
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=editCat(catImages[currentCat][0],catID,config)
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==13:     # create catagory
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=createCat(catImages[currentCat][0],catID,config)
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==14:     # search requested

        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)

        results=searchQuery(searchText,searchMode,catImages[currentCat][0],item[1],config)
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(results))

        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        cancelAction=14
        
        headerWidths=getCatColWidths(resultHeader,config)
        resultTable=catTable(resultData,catImages[currentCat][0],resultHeader,headerWidths,config)
        
    elif action==15:         # show note/media
        if mediaID[0]!="I":
            catID=mediaID
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)        
        results=mediaQuery(mediaID,config)
        
        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        
        headerWidths=getMediaColWidths(req,config)
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(cookieID))
        #~ resultTable=mediaTable(resultData,cookieID['kookyID'],mediaID,config)
        resultTable=mediaTable(resultData,cookieID,mediaID,config)
        
    elif action==16:     # edit media
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=editMedia(mediaID,catID,item,config)
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]
        catID=result[4]

    elif action==17:     # create media
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=createMedia(mediaID,catID,item,config)
        #~ util.redirect(req,"testValue.py/testvalue?test="+repr(result))
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]
        #~ catID=result[4]
        
    elif action==20:     # about 
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
         
        results=aboutInfo(config)
        # parse the results list
        caption=results[0]
        resultHeader=results[1]
        resultData=results[2]
        
        resultTable=aboutTable(resultData,config)
        
    elif action==21:     #edit config    
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=editConfig(req,config)
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]
        
    elif action==22:     #create config    
        itemSelect=itemForm(item[4],currentItem)
        catSelect=catForm(catImages,currentCat)
        catImage=catImages[currentCat][1]
        search=searchForm(searchText)
        result=createConfig(req,config)
        
        # parse the results list
        caption=result[0]
        resultHeader=result[1]
        resultTable=result[2]

    elif action==100:     # configure dialog
        # the emergency configuration dialog
        # when something is wrong in the config.txt file
        # the actual branch is done below
        pass

    else:               # no action - use defaults
        if config['lastUpdate']:
            
            itemID,mediaID=lastUpdate(config)
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(itemID)+repr(mediaID))
            item=itemData2(itemID,config)
            currentItem=indexItem(item,itemSelected,action)
            itemSelect=itemForm(item[4],currentItem)
            itemImage=itemImg(itemImage,item,config)
            catImages=catImgs(config)
            currentCat=0
            catSelect=catForm(catImages,currentCat)
            catImage=catImages[currentCat][1]
            search=searchForm(searchText)
            results=mediaQuery(mediaID,config)
            
            # parse the results list
            #~ cookieIDtext=kooky2.myCookies(req,'','','','')#['kookyID']

            caption="Most Recent Entry: "+results[0]
            resultHeader=results[1]
            resultData=results[2]
            
            headerWidths=getMediaColWidths(req,config)
            #~ data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])
            #~ username=data['username']
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(data))
            resultTable=mediaTable(resultData,cookieID,mediaID,config)
            
        else:
            
            item=itemData(currentItem,config)
            #~ util.redirect(req,"testValue.py/testvalue?test="+repr(currentItem))
            currentItem=indexItem(item,itemSelected,action)
            itemSelect=itemForm(item[4],currentItem)
            itemImage=itemImg(itemImage,item,config)
            catImages=catImgs(config)
            catSelect=catForm(catImages,currentCat)
            catImage=catImages[currentCat][1]
            search=searchForm(searchText)
            results=itemQuery(currentItem,item,config)
            cleanTmp(config)
            
            # parse the results list
            caption=results[0]
            resultHeader=results[1]
            resultData=results[2]
            
            resultTable=itemTable(resultData,config)
    
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
            'catID':catID,\
            'cancelAction':cancelAction,\
            'username':username,\
            'userpass':userpass,\
            'results':results\
            }

        kookied=kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])
#        util.redirect(req,"testValue.py/testvalue?test="+"kooky "+repr((relatedCat)))
        
        # set the template name
        mainForm='templates/main3.html'
        # check for an item related cat record to enable/disable delete function
        relatedCat=relatedRecords(currentItem,config)

        # the dic of values to pass to the html page
        vars['action']=action
        vars['popup']=popup
        vars['relatedCat']=relatedCat
        vars['dogleg']=username
        vars['cancelAction']=str(cancelAction)
        vars['error']=error
        vars['configDB']=config['dbname']
        vars['headerWidths']=headerWidths
        vars['mediaTable']=config['mediaTable']
        vars['catSelect']=catSelect
        vars['itemSelect']=itemSelect
        vars['catImages']=catImages
        vars['itemImage']=itemImage
        vars['caption']=caption
        vars['resultHeader']=resultHeader
        vars['resultTable']=resultTable
        vars['activeForm']=activeForm
        vars['mainTitle']=item[0]
        vars['mediaID']=mediaID
        vars['itemID']=item[1]
        vars['catID']=catID
        vars['currentItem']=str(currentItem)
        vars['currentCat']=str(currentCat)
        vars['search']=search
        vars['displayname']=config['displayname']
        vars['displaynamelocation']=config['displaynamelocation']
        vars['displaylogo']=config['displaylogo']

    else:
        mainForm='templates/conf.html'
        
        vars['message1']="THIS IS A DEFAULT CONFIGURATION DIALOG"
        vars['message2']="EITHER SOMETHING IS WRONG IN THE CONFIGURATION FILE"
        vars['message3']="A CRITICAL VALUE HAS CHANGED AND THE PROGRAM CAN'T START"
        vars['message4']="CHECK THE VALUES BELOW AND EDIT THEM AS NEEDED"
        vars['message5']="********************************************************"

#    util.redirect(req,"testValue.py/testvalue?test="+repr(resultHeader))

    # call the html doc passing it the data
    return psp.PSP(req,mainForm,vars=vars)



# ===============================================================
#               support functions
#

############ search functions
    
def searchQuery(searchText,searchMode,categoryName,itemID,config):
            
    selectFields,catHeader,booleanFields=catColumns(categoryName,itemID,config)
    itemFullTextCols,catFullTextCols,mediaFullTextCols=getFullTextCols(config)
    
            
    if searchMode:
        catFullTextCols=catFullTextCols+booleanFields
        mode=' IN BOOLEAN MODE'
    else:
        mode=""
        
    # all searchMode does is add some search fields and change the mode to boolean.

    if itemID=='0': #All_Items
        if categoryName[:3]=='All':
            if searchText: #ok
                # the  search query that searches all the category records for all the items for searchtext
                # all_items, all_cats,  searchText
                q='select distinct '+selectFields+\
                ' from '+config['catTable']+\
                ' left join '+config['itemTable']+' on '+\
                config['catTable']+'.'+config['itemIDfield']+'='+config['itemTable']+'.'+config['itemIDfield']+\
                ' left join '+config['mediaTable']+' on '+\
                config['mediaTable']+'.'+config['catIDfield']+'='+config['catTable']+'.'+config['catIDfield']+\
                ' where '+ '(MATCH ('+catFullTextCols+') AGAINST ("'+searchText+'"'+mode+')'+\
                ' or MATCH ('+itemFullTextCols+') AGAINST ("'+searchText+'"'+')'+\
                ' or MATCH ('+mediaFullTextCols+') AGAINST ("'+searchText+'"'+'))'+\
                " order by "+config['orderbyField']+" desc"
                
            else: #ok
                # get all records for all items
                # all_items, all_cats, NO searchText
                q='select '+selectFields+' from '+config['catTable']+\
                ' left join '+config['itemTable']+' on '+\
                config['catTable']+'.'+config['itemIDfield']+\
                '='+config['itemTable']+'.'+config['itemIDfield']+\
                " order by "+config['orderbyField']+" desc"

        else:
            if searchText: #ok
                # all_items, selected_cat, searchText
                q='select distinct '+selectFields+\
                ' from '+config['catTable']+\
                ' left join '+config['mediaTable']+' on '+\
                config['mediaTable']+'.'+config['catIDfield']+'='+config['catTable']+'.'+config['catIDfield']+\
                ' left join '+config['itemTable']+' on '+\
                config['catTable']+'.'+config['itemIDfield']+\
                '='+config['itemTable']+'.'+config['itemIDfield']+\
                ' where '+config['catField']+'="'+categoryName+'"'+\
                ' and (MATCH ('+catFullTextCols+') AGAINST ("'+searchText+'"'+mode+')'+\
                ' or MATCH ('+itemFullTextCols+') AGAINST ("'+searchText+'"'+')'+\
                ' or MATCH ('+mediaFullTextCols+') AGAINST ("'+searchText+'"'+'))'+\
                " order by "+config['orderbyField']+" desc"

            else: #ok
                # get records in this category all items
                # all_items, selected_cat, NO searchText
                q='select '+selectFields+' from '+config['catTable']+\
                ' left join '+config['itemTable']+' on '+\
                config['catTable']+'.'+config['itemIDfield']+\
                '='+config['itemTable']+'.'+config['itemIDfield']+\
                ' where '+config['catField']+'="'+categoryName+'"'+\
                " order by "+config['orderbyField']+" desc"
            

    else: # selected_item
        if categoryName[:3]=='All':
            if searchText: #ok
                # the  category search limited to the selected item and the search text
                # selected_item, all_cats, searchText
                q='select distinct '+selectFields+' from '+config['catTable']+\
                ' left join '+config['mediaTable']+' on '+\
                config['mediaTable']+'.'+config['catIDfield']+'='+config['catTable']+'.'+config['catIDfield']+\
                ' where '+config['catTable']+'.'+config['itemIDfield']+'="'+itemID+'"'\
                ' and (MATCH ('+catFullTextCols+') AGAINST ("'+searchText+'"'+mode+')'+\
                ' or MATCH ('+config['mediaTable']+') AGAINST ("'+searchText+'"'+'))'+\
                " order by "+config['orderbyField']+" desc"
                
            else: #ok
                # the category search limited to the selected item, but not limited by search text
                # selected_item, all_cats,  NO searchText
                q='select '+selectFields+' from '+config['catTable']+\
                ' where '+config['catTable']+'.'+config['itemIDfield']+'="'+itemID+'"'+\
                " order by "+config['orderbyField']+" desc"
                
        else:
            if searchText: #ok
                # the normal search limited to the selected item and selected category and searchText
                # selected_item, selected_cat,  searchText                    
                q='select distinct '+selectFields+' from '+config['catTable']+\
                ' left join '+config['mediaTable']+' on '+\
                config['mediaTable']+'.'+config['catIDfield']+'='+config['catTable']+'.'+config['catIDfield']+\
                ' where '+config['catField']+'="'+categoryName+'"'+\
                ' and '+config['catTable']+'.'+config['itemIDfield']+'="'+itemID+'"'\
                ' and (MATCH ('+catFullTextCols+') AGAINST ("'+searchText+'"'+mode+')'+\
                ' or MATCH ('+config['mediaTable']+') AGAINST ("'+searchText+'"'+'))'+\
                " order by "+config['orderbyField']+" desc"
                
            else: #ok
                # the normal search limited to the selected item and selected category only
                # selected_item, selected_cat, NO searchText                    
                q='select '+selectFields+' from '+config['catTable']+\
                ' where '+config['catField']+'="'+categoryName+'"'+\
                ' and '+config['catTable']+'.'+config['itemIDfield']+'="'+itemID+'"'+\
                " order by "+config['orderbyField']+" desc"
                            
    qresult1=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    if itemID=='0':
        qresult2=[]
        for thisRow in qresult1:
            uniqueField=""
            row2=[thisRow[0]]
            for thisCol in range(1,len(config['itemUniqueID'])+1):
                uniqueField=uniqueField+str(thisRow[thisCol])+" "
            row2.append(uniqueField)
            for thisCol in range(len(config['itemUniqueID'])+1,len(thisRow)):
                row2.append(str(thisRow[thisCol]))
            qresult2.append(row2)
    else:
        qresult2=qresult1
            
            
    if isinstance(qresult1,tuple):
        catCaption=str(len(qresult2))+' records matching search="'+searchText
        #~ catCaption=q

    else:
        # the query failed
        catCaption='No results for this search query!'
        #~ catHeader=q
    
    return (catCaption,catHeader,qresult2,"cat")

def getFullTextCols(config):
    
    # fulltext cols for itemTable
    q="show index from "+config['itemTable']
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    itemFullTextCols=""
    for thisCol in qresult:
        if thisCol[10]=="FULLTEXT":
            itemFullTextCols=itemFullTextCols+config['itemTable']+'.'+thisCol[4]+","
        mode=''
    itemFullTextCols=itemFullTextCols[:-1]
    
    # fulltext cols for catTable
    q="show index from "+config['catTable']
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    catFullTextCols=""
    for thisCol in qresult:
        if thisCol[10]=="FULLTEXT":
            catFullTextCols=catFullTextCols+config['catTable']+'.'+thisCol[4]+","
        mode=''
    catFullTextCols=catFullTextCols[:-1]
    
    # fulltext cols for mediaTable
    q="show index from "+config['mediaTable']
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    mediaFullTextCols=""
    for thisCol in qresult:
        if thisCol[10]=="FULLTEXT":
            mediaFullTextCols=mediaFullTextCols+config['mediaTable']+'.'+thisCol[4]+","
        mode=''
    mediaFullTextCols=mediaFullTextCols[:-1]
    
    return(itemFullTextCols,catFullTextCols,mediaFullTextCols)
    
def searchForm(searchText):

    moreInput=strict401gen.Input(type='checkbox',checked='',name='searchMode',title="Boolean Search",Class="editfield searchInput")
    searchInput=strict401gen.Input(type='text',llabel="Search",value=searchText,size="15",maxlength="20",name='searchText',title="Enter text to Search for.",Class="editfield searchField searchInput")
    searchButton=strict401gen.Input(type="image",name="searchbutton",srcImage="images/search2.png",alt="Search",title="Submit Search",Class="searchbutton searchSubmit")
    
    form=strict401gen.Form(submit="",name='newSearch',cgi='index?action=14')
    form.append("<p>")
    form.append(moreInput)
    form.append(searchInput)
    form.append(searchButton)
    
    return(form)
    
def moreForm():

    moreInput=strict401gen.Input(type='checkbox',name='searchMode',Class="topfield")
    form=strict401gen.Form(submit="",name='moreSearch',cgi='index?action=14')
    form.append(moreInput)
    
    return(form)
    



############ item functions

def writeImgs(config):
    
    # first remove all images - except the default
    try:
        imageFiles=os.listdir(config['itemImagePath'])
    except:
        imageFiles=[]
        
    for thisimage in imageFiles:
        try:
            # dont remove the default.jpg image or All image
            if "default" not in thisimage:
                if  string.split(thisimage,'.')[0]!='0':
                    os.remove(config['itemImagePath']+thisimage)
        except:
            pass
        
    # write all item images to disk
    q="select "+config['itemTable']+"."+config['itemIMGfield']+","\
    +config['itemTable']+"."+config['itemIDfield']+" from "+config['itemTable']
    
    imageData=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    imagesondisk=[]

    # loop thru each record, make sure it's a valid img b4 writting it
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
                imgFile=open(config['itemImagePath']+imagename,"wb")
                imgFile.write(thisImage[0])
                imgFile.close()
            except:
                pass
                
            imagesondisk.append(str(thisImage[1])+'*'+imagename)
            
    return imagesondisk
    
def itemImg(itemImage,item,config):
    
    try:
        imageFiles=os.listdir(config['itemImagePath'])
    except:
        imageFiles=[]
    
    imgName=str(item[2]).lower()
    itemImage=''
    
    for thisImg in imageFiles:
        fileName=string.split(thisImg,".")[0]
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
                if itemSelected in itemList[thisItem]:
                    currentItem=thisItem
    # no change
    else:
        currentItem=item[5]

    
    return currentItem

def itemData(currentItem,config):
    
    selected=""
    for thisField in config['itemUniqueID']:
        selected=selected+config['itemTable']+"."+thisField+","
    
    # get item item data
    q="select "+selected\
    +config['itemTable']+"."+config['itemIDfield']+" from "+config['itemTable']

    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    itemIDs=[]
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
        
    mainTitle=''
    for thisItem in range(0,len(itemList[0])-1):
        mainTitle=mainTitle+" "+str(itemList[currentItem][thisItem])
        
    itemID=itemList[currentItem][-1]
    imgName=itemList[currentItem][-1]
    itemCount=len(itemList)
    
    item=[mainTitle,itemID,imgName,itemCount,itemList,currentItem]

    return item
        
def itemData2(itemID,config):
    
    selected=""
    for thisField in config['itemUniqueID']:
        selected=selected+config['itemTable']+"."+thisField+","
    
    # get item item data
    q="select "+selected\
    +config['itemTable']+"."+config['itemIDfield']+" from "+config['itemTable']

    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    itemIDs=[]
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
    
def itemQuery(currentItem,item,config):

    itemID=str(item[1])
    mainTitle=str(item[0])
    q="show columns from "+config['itemTable']
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
    selectCols=string.join(colNames,",")

    if currentItem>0:

        # get data
        q='select '+selectCols+' from '+config['itemTable']+' where '+config['itemIDfield']+'="'+itemID+'"'
        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        
    else:

        selectCols=idCol+','+string.join(config['allItems'],",")
        q='select '+selectCols+' from '+config['itemTable']+\
        ' order by '+config['allItems'][0]
        
        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
        
    # convert the results to a list of lists
    qresult=list(qresult)
    
    # check for notes

    q2='select '+config['mediaTable']+'.'+config['itemIDfield']+' from '+config['mediaTable']+\
    ' left join '+config['itemTable']+' on '+\
    config['mediaTable']+'.'+config['itemIDfield']+'='+config['itemTable']+'.'+config['itemIDfield']+\
    ' where '+config['itemTable']+'.'+config['itemIDfield'] +'="'+str(qresult[0])+'"'

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
        for thisName in config['allItems']:
            header.append(thisName.upper())

    return (caption,header,qresult,'item')

def itemAllTable(itemData,categoryName,header,colWidths,config):

    endWidth="20"

    itemTable=strict401gen.TableLite(border=0,CLASS='resultstable',cellpadding="",cellspacing="1")

    if itemData:
        
        rowcolor='#FFFF99'

        for thisRecord in itemData:
            
            if rowcolor=='#FFFF99':
                rowcolor='#FFFFCC'
            else:
                rowcolor='#FFFF99'

            itemRow=strict401gen.TR(style="background-color:"+rowcolor)
            recNum=''
            
            # get note data
            q2='select '+config['mediaTable']+'.'+config['mediaIDfield']+' from '+config['mediaTable']+\
            ' left join '+config['itemTable']+' on '+\
            config['mediaTable']+'.'+config['itemIDfield']+'='+config['itemTable']+'.'+config['itemIDfield']+\
            ' where '+config['itemTable']+'.'+config['itemIDfield']+'="'+str(thisRecord[0])+'"'

            noteID=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
            try:
                note=noteID[0]
            except:
                note=""
            
            for thisCol in range(0,len(thisRecord)):

                if thisCol==0:
                    recNum=str(thisRecord[thisCol])
                    gotoImage=strict401gen.Image(("images/left2.png","16","16"),alt="Goto",name="goto",title="Goto Item Record")
                    itemRow.append(strict401gen.TD(strict401gen.Href("index?item="+str(thisRecord[thisCol]),gotoImage),Class="resultcol0"))

                elif thisRecord[thisCol]:
                    itemRow.append(strict401gen.TD(thisRecord[thisCol],Class="resultcol"+str(thisCol)))
                else:
                    itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),Class="resultcol"+str(thisCol)))
                    
            if not note:
                noteimage=strict401gen.Image(("images/add.png","16","16"),alt="Add",title="Add a "+config['mediaTable'])
                itemRow.append(strict401gen.TD(strict401gen.Href("index?media=Inew"+recNum,noteimage),Class="resultcol7"))
            else:
                noteimage=strict401gen.Image(("images/right2.png","16","16"),name=str(thisRecord[0]),alt='View',title="View "+config['mediaTable'])
                itemRow.append(strict401gen.TD(strict401gen.Href("index?media=I"+recNum,noteimage),Class="resultcol7"))
                    
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
        rowcolor='#FFFF99'
        
        itemRow=strict401gen.TR(style="background-color:"+rowcolor)
        if itemData:
            itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="1"))
        else:
            itemRow.append(strict401gen.TD(strict401gen.RawText("No records found "),colspan="1"))
        itemTable.append(itemRow)
        
    return itemTable
    
def itemTable(itemData,config):
    
    q="show columns from "+config['itemTable']
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
        
    if itemData:
        
        resultTable=strict401gen.TableLite(border="0",CLASS='resultstable')
        rowcolor='#FFFF99'
        
        for thisCol in range(1,len(colNames)):
            if rowcolor=='#FFFF99':
                rowcolor='#FFFFCC'
            else:
                rowcolor='#FFFF99'

            itemRow=strict401gen.TR(style="background-color:"+rowcolor)
            itemRow.append(strict401gen.TD(colNames[thisCol],style="width:385px;"))
            
            if itemData[thisCol]:
                itemRow.append(strict401gen.TD(itemData[thisCol],style="width:383px;"))
            else:
                itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),style="width:400px;"))
        
            resultTable.append(itemRow)
    else:
        # the query failed
        caption="query failed"
        resultTable=strict401gen.Table(caption,border=0,heading=['Error','Result','Query'],id='results',\
            column1_align="left",cell_align="left",cell_padding="0",\
            cell_spacing="0",body_color=['#FFFF99','#FFFFCC'],heading_color=['#FFFF99'])

        resultTable.body.append(['no query results?',str(qresult),q])
    
    return (resultTable)

def itemForm(itemList,currentItem):

    itemList2=strict401gen.Select(itemList,onChange="javascript:document.newItem.submit();",size=1,name='item',selected=itemList[currentItem],Class="topfield")
    form=strict401gen.Form(submit="",name='newItem',cgi='index?action=4')
    form.append(itemList2)

    return(form)

def createItem(currentItem,item,config):

    itemID=str(item[1])
    mainTitle=str(item[0])
    cols=[]
    colNames=[]

    q="show columns from "+config['itemTable']
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
    
    itemTable=strict401gen.TableLite(border=0,Class="edittable")
    
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
            itemRow.append(strict401gen.TD(strict401gen.Select(enumList,name=thisField[0],Class="editfield")))
            
        elif 'set(' in thisField[1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][4:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],multiple=1,size=len(setList),Class="editfield")))                    
            
        elif 'date' in thisField[1]:
            x=string.strip(str(datetime.date.today()))
            itemRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=thisField[0],maxlength="10",Class="editfield dataInput")))

        elif 'text' in thisField[1]:
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Textarea(name=thisField[0],Class="editfield dataInput")))
            
        elif 'blob' in thisField[1]:
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Input(type='file',name=thisField[0],size="10",Class="editfield")))
            
        else:
            itemRow.append(strict401gen.TD(thisField[0],Class='editLabel'))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],maxlength=maxlen,Class="editfield dataInput")))
            
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
    mainTitle=str(item[0])
    cols=[]
    colNames=[]
    
    # get the column  names
    q="show columns from "+config['itemTable']
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

    selectCols=string.join(colNames,",")
    q='select '+selectCols+' from '+config['itemTable']+\
    ' where '+config['itemIDfield']+'="'+itemID+'"'
    values=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    itemTable=strict401gen.TableLite(border=0,Class="edittable")
    
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
            itemRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=values[0][thisField],name=cols[thisField][0],Class="editfield")))
            
        elif 'set(' in cols[thisField][1]:
            setList=cols[thisField][1].split(",")
            setList[0]=setList[0][4:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Select(setList,name=cols[thisField][0],multiple=1,size=len(setList),Class="editfield")))                    
              
        elif 'text' in cols[thisField][1]:
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Textarea(values[0][thisField],name=cols[thisField][0],Class="editfield dataInput")))
            
        elif 'date' in cols[thisField][1]:
            if not values[0][thisField] or values[0][thisField]=="None":
                x=string.strip(str(datetime.date.today()))
            else:
                x=values[0][thisField]
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=cols[thisField][0],maxlength="10",Class="editfield dataInput")))

        elif 'blob' in cols[thisField][1]:
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],size="10",Class="editfield")))
            
        else:
            itemRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            itemRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))
            
        if not count%2:
            itemTable.append(itemRow)
            itemRow=strict401gen.TR()
        elif count==len(cols):
            itemRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2"))
            itemTable.append(itemRow)
            
    caption='Update  the information for "'+config['dbname']+'"'
    header=formbuttons('update')
    
    return (caption,header,itemTable,'item')

def deleteItem(currentItem,item,config):
    
    itemID=str(item[1])
    mainTitle=str(item[0])

############ category functions

def catImgs(config):

    catImagePath=config['catImagePath']+config['dbname']+'/'
    images=os.listdir(catImagePath)    
    cats=[]
    catImages=[]
    
    q='describe '+config['catTable']+' '+config['catField']
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

    selectFields,catHeader,booleanFields=catColumns(categoryName,itemID,config)

    if itemID=='0':
        if categoryName[:3]=='All': # will NOT show results
            # get all records for all items
            # all_items, all_cats, NO searchText
            q='select '+selectFields+' from '+config['catTable']+\
            ' left join '+config['itemTable']+' on '+\
            config['catTable']+'.'+config['itemIDfield']+\
            '='+config['itemTable']+'.'+config['itemIDfield']+\
            " order by "+config['orderbyField']+" desc"

        else:
            # get records in this category all items
            q='select '+selectFields+' from '+config['catTable']\
            +' left join '+config['itemTable']+' on '\
            +config['catTable']+'.'+config['itemIDfield']+'='+config['itemTable']+'.'+config['itemIDfield']\
            +' where '+config['catField']+'="'+categoryName+'"'\
            +" order by "+config['orderbyField']+" desc"
        
    else:
        if categoryName[:3]=='All':
            # get all records
            q='select '+selectFields+' from '+config['catTable']\
            +' where '+config['catTable']+'.'+config['itemIDfield']+'="'+itemID+'"'\
            +" order by "+config['orderbyField']+" desc"        
        else:
            # get records in this category this item only
            q='select '+selectFields+' from '+config['catTable']\
            +' where '+config['catField']+'="'+categoryName+'"'\
            +' and '+config['catTable']+'.'+config['itemIDfield']+'="'+itemID+'"'\
            +" order by "+config['orderbyField']+" desc"
                
    qresult1=db.dbConnect(config['selectedHost'],config['dbname'],str(q),0)

    if itemID=='0':
        qresult2=[]
        for thisRow in qresult1:
            uniqueField=""
            row2=[thisRow[0]]
            for thisCol in range(1,len(config['itemUniqueID'])+1):
                uniqueField=uniqueField+str(thisRow[thisCol])+" "
            row2.append(uniqueField)
            for thisCol in range(len(config['itemUniqueID'])+1,len(thisRow)):
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

def catTable(catData,categoryName,header,colWidths,config):

    endWidth="20"
    
    if config['itemTable'].upper() in header:
        searchType='booleanSearch'
    elif config['catField'].upper() in header:
        searchType='allSearch'
    else:
        searchType=''
    
    catTable=strict401gen.TableLite(border=0,CLASS='resultstable',cellpadding="",cellspacing="1")

    if catData:
        
        rowcolor='#FFFF99'

        for thisRecord in catData:
            
            if rowcolor=='#FFFF99':
                rowcolor='#FFFFCC'
            else:
                rowcolor='#FFFF99'

            catRow=strict401gen.TR(style="background-color:"+rowcolor)
            recNum=''
            
            # get note data
            q2='select '+config['mediaTable']+'.'+config['mediaIDfield']+' from '+config['mediaTable']+\
            ' left join '+config['catTable']+' on '+\
            config['mediaTable']+'.'+config['catIDfield']+'='+config['catTable']+'.'+config['catIDfield']+\
            ' where '+config['catTable']+'.'+config['catIDfield']+'="'+str(thisRecord[0])+'"'

            noteID=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
            try:
                note=noteID[0]
                deleteImg="images/delete-inactive.png"
                delToolTip=""
            except:
                note=""
                deleteImg="images/delete.png"
                delToolTip="Delete Record"
                
            for thisCol in range(0,len(thisRecord)):

                if thisCol==0:
                    recNum=str(thisRecord[thisCol])

                    toolTable=strict401gen.TableLite(border=0,CLASS='',cellpadding="0",cellspacing="0")
                    toolRow=strict401gen.TR(style="background-color:"+rowcolor)
                    # column for the edit button
                    if searchType=='booleanSearch':
                        editImage=strict401gen.RawText("&nbsp;")
                    elif searchType=="allSearch":
                        editImage=strict401gen.Image(("images/edit.png","16","16"),alt="Edit",name="Edit",title="Edit Record")
                    else:
                        editImage=strict401gen.Image(("images/edit.png","16","16"),alt="Edit",name="Edit",title="Edit Record")
                    toolRow.append(strict401gen.TD(strict401gen.Href("index?edit="+str(thisRecord[thisCol]),editImage),valign='top',colspan="1",Class="toolcol0"))
                    toolTable.append(toolRow)
                    toolRow=strict401gen.TR(style="background-color:"+rowcolor)
                    
                    # column for the delete link
                    delimage=strict401gen.Image((deleteImg,str(endWidth),str(endWidth)),alt="Del",name="Del",title=delToolTip)
                    if delToolTip:
                        toolRow.append(strict401gen.TD(strict401gen.Href("index?popup=96&catID="+str(thisRecord[thisCol]),delimage),valign='top',colspan="1",Class="toolcol0"))
                    else:
                        toolRow.append(strict401gen.TD(delimage,valign='top',colspan="1",Class="toolcol0"))
                    toolTable.append(toolRow)                    
                    catRow.append(strict401gen.TD(toolTable,valign='top',colspan="1",Class="toolcol0"))
                    
                elif thisRecord[thisCol]:
                    catRow.append(strict401gen.TD(thisRecord[thisCol],Class="resultcol"+str(thisCol)))
                else:
                    catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),Class="resultcol"+str(thisCol)))

            if not note:
                noteimage=strict401gen.Image(("images/add.png","16","16"),alt="Add",title="Add a "+config['mediaTable'])
                catRow.append(strict401gen.TD(strict401gen.Href("index?media=new"+recNum,noteimage),Class="resultcol7"))
            else:
                noteimage=strict401gen.Image(("images/right2.png","16","16"),name=str(thisRecord[0]),alt='View',title="View "+config['mediaTable'])
                catRow.append(strict401gen.TD(strict401gen.Href("index?media="+recNum,noteimage),Class="resultcol7"))
                    
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
        rowcolor='#FFFF99'
        
        catRow=strict401gen.TR(style="background-color:"+rowcolor)
        if catData:
            catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),colspan="1"))
        else:
            catRow.append(strict401gen.TD(strict401gen.RawText("No records found for "+categoryName),colspan="1"))
        catTable.append(catRow)
        
    return catTable
    
def catColumns(categoryName,itemID,config):

    colNames=[]
    selectFields=''
    catHeader=[]
    booleanFields=''
    
    q="show columns from "+config['catTable']
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
            
        # add enum cols to boolean search
        if 'enum(' in thisCol[1]:
            booleanFields=booleanFields+','+thisCol[0]
            
    colNames.insert(0,idCol)

    if itemID=='0':
        if categoryName[:3]=="All":
            # header for all items, all categories
            catHeader=[config['itemTable'].upper()]
            for thisField in config['catSearchFields']:
                catHeader.append(thisField.upper())
                
            # selected fields for all items, all categories
            selectFields=config['catTable']+"."+config['catIDfield']+","
            for thisCol in config['itemUniqueID']:
                selectFields=selectFields+config['itemTable']+'.'+thisCol+","
            for thisCol in config['catSearchFields']:
                selectFields=selectFields+config['catTable']+'.'+thisCol+","
            selectFields=selectFields[:-1]

        else:
            if config['catField'] in config['catSearchFields']:
                config['catSearchFields'].remove(config['catField'])
                
            # header for all items, one category
            catHeader=[config['itemTable'].upper()]
            for thisField in config['catSearchFields']:
                catHeader.append(thisField.upper())
                
            # selected fields for all items, one category
            selectFields=config['catTable']+"."+config['catIDfield']+","
            for thisCol in config['itemUniqueID']:
                selectFields=selectFields+config['itemTable']+'.'+thisCol+","
            for thisCol in config['catSearchFields']:
                selectFields=selectFields+config['catTable']+'.'+thisCol+","
            selectFields=selectFields[:-1]
                
    else:
        if categoryName[:3]=='All':
            # header for one item, all categories
            for thisCol in range(1, len(colNames)):
                catHeader.append(colNames[thisCol].upper())
            
            # selected fields for one item, all categories
            for thisCol in colNames:
                selectFields=selectFields+config['catTable']+'.'+thisCol+","
            selectFields=selectFields[:-1]
            
        else:
            if config['catField'] in colNames:
                colNames.remove(config['catField'])
                
            # header for one item, one categories
            for thisCol in range(1, len(colNames)):
                catHeader.append(colNames[thisCol].upper())
            
            # selected fields for one item, one category
            for thisCol in colNames:
                selectFields=selectFields+config['catTable']+'.'+thisCol+","
            selectFields=selectFields[:-1]
            
    return (selectFields,catHeader,booleanFields)
    
def catColumnsold(categoryName,itemID,config):

    colNames=[]
    selectFields=''
    catHeader=[]
    booleanFields=''
    
    q="show columns from "+config['catTable']
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    # filter out certain cols 
    for thisCol in qresult:
        if 'timestamp'in thisCol[1]:
            pass
        elif 'text' in thisCol[1]:
            pass
        elif thisCol[0]==config['catField'] and itemID!='0':
            pass
        elif thisCol[3]=="PRI":
            idCol=thisCol[0]
        elif thisCol[0] in config['primaries']:
            pass
        else:
            colNames.append(thisCol[0])
            
        # add enum cols to boolean search
        if 'enum(' in thisCol[1]:
            booleanFields=booleanFields+','+thisCol[0]
            
    colNames.insert(0,idCol)

    if itemID=='0':
        # header for combo search results
        catHeader=[config['itemTable'].upper()]
        for thisField in config['catSearchFields']:
            catHeader.append(thisField.upper())
            
    elif categoryName[:3]=='All':
        # header for cat search/query where catField must be included
        for thisCol in range(1, len(colNames)):
            catHeader.append(colNames[thisCol].upper())
        #~ catHeader.insert(0,config['catField'].upper())
        catHeader.append(config['catField'].upper())
    else:
        # standard header for cat search/query
        for thisCol in range(1, len(colNames)):
            catHeader.append(colNames[thisCol].upper())
            
    if itemID=='0':
        # fields to select for boolean search
        selectFields=config['catTable']+"."+config['catIDfield']+","
        for thisCol in config['itemUniqueID']:
            selectFields=selectFields+config['itemTable']+'.'+thisCol+","
        for thisCol in config['catSearchFields']:
            selectFields=selectFields+config['catTable']+'.'+thisCol+","
        selectFields=selectFields[:-1]
    elif categoryName[:3]=='All':
        # fields to select for All_Records cat query
        #~ colNames.insert(1,config['catField'])
        colNames.append(config['catField'])
        for thisCol in colNames:
            selectFields=selectFields+config['catTable']+'.'+thisCol+","
        selectFields=selectFields[:-1]
    else:
        # fields to select for cat search/query
        for thisCol in colNames:
            selectFields=selectFields+config['catTable']+'.'+thisCol+","
        selectFields=selectFields[:-1]
    
    return (selectFields,catHeader,booleanFields)
        
def catForm(catImages,currentCat):
        
    catList=strict401gen.Select(catImages,onChange="javascript:document.newCat.submit();",size=1,name='category',selected=catImages[currentCat],Class="topfield")
    form=strict401gen.Form(submit="",name='newCat',cgi='index?action=8')
    form.append(catList)

    return(form)

def createCat(categoryName,item,config):

    cols=[]

    q="show columns from "+config['catTable']
    allCols=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    for thisCol in allCols:
        if thisCol[0] in config['primaries']:
            pass
        elif 'timestamp' in thisCol[1]:
            pass
        elif config['catField'] in thisCol[0]:
            pass            
        elif config['owner'] in thisCol[0]:
            pass
        else:
            cols.append(thisCol)

    catTable=strict401gen.TableLite(border=0,Class="edittable")
    
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
            catRow.append(strict401gen.TD(strict401gen.Select(enumList,name=thisField[0],Class="editfield")))
            
        elif 'set(' in thisField[1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],multiple=1,size=len(setList),Class="editfield")))                    
            
        elif 'text' in thisField[1]:
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Textarea(name=thisField[0],Class="editfield dataInput")))
            
        elif 'blob' in thisField[1]:
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type='file',name=thisField[0],Class="editfield")))
            
        elif 'date' in thisField[1]:
            x=string.strip(str(datetime.date.today()))
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=thisField[0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in thisField[1]:
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        elif 'float' in thisField[1]:
            maxlen=maxlen.split(',')[0]              
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],maxlength="6",Class="editfield dataInput")))

        else: # char fields
            if thisField[4]:
                defaultValue=thisField[4]
            else:
                defaultValue=''
            catRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(value=defaultValue,type="text",name=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            catTable.append(catRow)
            catRow=strict401gen.TR()
        elif count==len(cols):
            catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2"))
            catTable.append(catRow)
                
    caption='Insert the information for "'+categoryName+'" '+config['catTable']
    header=formbuttons('create')
    
    return (caption,header,catTable,'cat')

def editCat(categoryName,catID,config):
    
    cols=[]
    colNames=[]
    
    # get the column  names
    q="show columns from "+config['catTable']
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
            elif config['catField'] in thisCol[0] :
                pass
            elif config['owner'] in thisCol[0]:
                pass
            else:
                cols.append(thisCol)
                colNames.append(thisCol[0])

    # get col values
    selectCols=string.join(colNames,",")
    q="select "+selectCols+" from "+config['catTable']+\
    " where "+config['catIDfield']+"='"+catID+"'"
    values=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    catTable=strict401gen.TableLite(border="0",Class="edittable")
    
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
            catRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=values[0][thisField],name=cols[thisField][0],Class="editfield")))
            
        elif 'set(' in cols[thisField][1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],multiple=1,size=len(setList),Class="editfield")))                    
        
        elif 'text' in cols[thisField][1]:
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Textarea(values[0][thisField],name=cols[thisField][0],Class="editfield dataInput")))
            
        elif 'blob' in cols[thisField][1]:
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],Class="editfield")))
        
        elif 'date' in cols[thisField][1]:
            if not values[0][thisField] or values[0][thisField]=="None":
                x=string.strip(str(datetime.date.today()))
            else:
                x=values[0][thisField]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=cols[thisField][0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in cols[thisField][1]:
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        elif 'float' in cols[thisField][1]:
            maxlen=maxlen.split(',')[0]
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        else: # char fields
            catRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            catRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            catTable.append(catRow)
            catRow=strict401gen.TR()
        elif count==len(cols):
            catRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2"))
            catTable.append(catRow)

    caption='Update the information for "'+categoryName+'" '+config['catTable']
    header=formbuttons('update')
    
    return (caption,header,catTable,'cat')

############ media functions

def mediaQuery(record,config):

    q="show columns from "+config['mediaTable']
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
        else:
            if 'date'in thisCol[1]:
                orderby=thisCol[0]
            colNames.append(thisCol[0])
    colNames.insert(0,idCol)    # for edit link
    
     # build the select fields for the media table query
    selectFields=""
    for thisField in colNames:
        selectFields=selectFields+config['mediaTable']+'.'+thisField+','
    selectFields=selectFields[:-1]
    
    if record[0]=="I":
        # this is an item note
        recordNum=record[1:]
        q='select '+selectFields +' from '+config['mediaTable']+\
        ' where '+config['mediaTable']+'.'+config["itemIDfield"]+'="'+recordNum+'"'
    else:
        # this is a category note
        recordNum=record
        q='select '+selectFields +' from '+config['mediaTable']+\
        ' where '+config['mediaTable']+'.'+config["catIDfield"]+'="'+recordNum+'"'
    
    if orderby:
        q=q+" order by `"+orderby+"` desc"

    
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    if record[0]=="I":
        # for an item caption
        q2='select '+string.join(config['itemUniqueID'],",")+' from '+\
        config['itemTable']+' where '+ config['itemIDfield']+'="'+recordNum+'"'

        header=db.dbConnect(config['selectedHost'],config['dbname'],q2,0)
        #~ mediaCaption=config['mediaTable']+'(s) for '+string.join(header[0]," ")
        mediaCaption=string.join(header[0]," ")
        mediaHeader=['Imedia']
        
    else:
        # for a category header
        q2='select '+config['catInfo']+' from '+\
        config['catTable']+' where '+ config['catIDfield']+'="'+recordNum+'"'
    
        header=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
        #~ mediaCaption=config['mediaTable']+'(s) for '+header[0]+' '
        mediaCaption=header[0]+' '
        mediaHeader=['media']
        
    return (mediaCaption,mediaHeader,qresult,'media')

def mediaTable(mediaData,cookieID,record,config):

    endWidth=16
    mediaTable=strict401gen.TableLite(border=0,CLASS='resultstable',cellpadding="10",cellspacing="0")
    
    rowcolor='#FFFF99'
    imageCount=0
    maxCols=len(mediaData[0])
    
    for thisRecord in mediaData:
        
        # display the owner at the top of the media if available
        # enabled for the 'read' db specifically
        if record[0]=="I":
            # this is an item note
            recordNum=record[1:]
            q='select '+config['owner'] +' from '+config['mediaTable']+\
            ' where '+config['mediaTable']+'.'+config["mediaIDfield"]+'="'+str(thisRecord[0])+'"'
        else:
            # this is a category note
            recordNum=record
            q='select '+config['owner']+' from '+config['mediaTable']+\
            ' where '+config['mediaTable']+'.'+config["mediaIDfield"]+'="'+str(thisRecord[0])+'"'
    
        owner=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        # try will fail if the table doesn't have an owner field
        try:
            owner=owner[0]
        except:
            owner=''
        
        if rowcolor=='#FFFF99':
            rowcolor='#FFFFCC'
        else:
            rowcolor='#FFFF99'
            
        # check to see if it's an Item record
        q="select "+config['itemIDfield']+" from "+config['mediaTable']+\
        " where "+config['mediaIDfield']+'="'+str(thisRecord[0])+'"'
        
        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        if qresult[0]:
            mediaType="I"
        else:
            mediaType=""

        mediaRow=strict401gen.TR(style="background-color:"+rowcolor)
        
        # record the number of cols with values
        colValues=0
        for thisCol in thisRecord:
            if thisCol:
                colValues=colValues+1
        
        # go through the cols, insert the data into the table
        for thisCol in range(0,len(thisRecord)):
            
            # if this col is an image set the image type
            try:
                imgType=imghdr.what('',thisRecord[thisCol])
                # force 3 char extention for windows
                if len(imgType)>3:
                    imgType="."+imgType[0:2]+imgType[-1:]
                else:
                    imgType="."+imgType
            except:
                imgType=''
            
            # test if col is binary - defaults to not binary
            isBinary=0
            try:
                if "\0" in thisRecord[thisCol]:
                    isBinary=1
                else:
                    isBinary=0
            except:
                isBinary=0

              
            if thisCol==0:
                
                toolTable=strict401gen.TableLite(border=0,CLASS='',cellpadding="0",cellspacing="0")
                # column for the edit button if not a All search
                toolRow=strict401gen.TR(style="background-color:"+rowcolor)
                edimage=strict401gen.Image(("images/edit.png",str(endWidth),str(endWidth)),alt="Edit",name="Edit",title="Edit Record")
                toolRow.append(strict401gen.TD(strict401gen.Href("index?medit="+mediaType+str(thisRecord[thisCol]),edimage),valign='top',colspan="1",Class="mediacol0"))
                toolTable.append(toolRow)
                # column for the delete button if not a All search
                toolRow=strict401gen.TR(style="background-color:"+rowcolor)
                delimage=strict401gen.Image(("images/delete.png",str(endWidth),str(endWidth)),alt="Del",name="Del",title="Del Record")
                toolRow.append(strict401gen.TD(strict401gen.Href("index?popup=97"+"&mediaID="+str(thisRecord[thisCol])+"&media="+str(record),delimage),valign='top',colspan="1",Class="mediacol0"))
                toolTable.append(toolRow)
                # add the buttons at col one
                mediaRow.append(strict401gen.TD(toolTable,valign='top',colspan="1",Class="mediacol0"))

            elif imgType :
                # if it's an image write it to disk so the program can load it
                if os.path.exists(config['mediaPath']+cookieID):
                    pass
                else:
                    os.mkdir(config['mediaPath']+cookieID)
                imageCount=imageCount+1
                # imagename must be unique
                imagename=config['dbname']+'-'+str(thisRecord[0])+'-'+str(imageCount)+imgType
                imgFile=open(config['mediaPath']+cookieID+'/'+imagename,"wb")
                imgFile.write(thisRecord[thisCol])
                imgFile.close()
                                    
                columns=1
                
                imageLink=strict401gen.Href("tmp/"+cookieID+'/'+imagename,strict401gen.Image("tmp/"+cookieID+'/'+imagename,alt="alt.img",Class="mediaimage"),onClick="window.open(this.href);return false;")
                mediaRow.append(strict401gen.TD(imageLink,colspan=str(columns),align="right",valign='top',Class="mediaimage"))
                
            elif isBinary:
                # this is a minimal branching for binary files not recognized as images
                # I've read that it gives false results for utf16 files, possibly other files too.
                # I just provide a download link
                if os.path.exists(config['mediaPath']+cookieID):
                    pass
                else:
                    os.mkdir(config['mediaPath']+cookieID)
                imageCount=imageCount+1
                # name must be unique
                binaryname=config['dbname']+'-'+str(thisRecord[0])+'-'+str(imageCount)+imgType
                binFile=open(config['mediaPath']+cookieID+'/'+binaryname,"wb")
                binFile.write(thisRecord[thisCol])
                binFile.close()
                                    
                columns=1
                
                text="Download Binary File"
                binaryLink=strict401gen.Href("tmp/"+cookieID+'/'+binaryname,text,onClick="window.open(this.href);return false;")
                mediaRow.append(strict401gen.TD(binaryLink,colspan=str(columns),align="right",valign='top',Class="mediaimage"))
                
            else:                           #thisRecord[thisCol]:
                # it's not an image, it's text or it's empty
                if thisRecord[thisCol]==None:
                    value=""
                else:
                    value=thisRecord[thisCol]

                columns=1
                
                text1=str(value)
                text2=text1.replace('\r\n','<BR>')
                text3=text2.replace('\n','<BR>')
                text=text3.replace('\r','<BR>')
                # make more room for large text cols
                if len(text)>15:
                    colClass="mediaCol1"
                else:
                    colClass="mediaCol2"
                if owner:  # special concern for the 'read' db
                    if thisCol==1:
                        text=owner.capitalize()+' writes:<BR><BR>'+text
#                mediaRow.append(strict401gen.TD(strict401gen.RawText(text),colspan=str(columns),valign='top',Class="mediacol1"))
                mediaRow.append(strict401gen.TD(strict401gen.RawText(text),colspan=str(columns),valign='top',Class=colClass))
        
        # add the row to the table
        mediaTable.append(mediaRow)
        
        # add a row to make sure the scroll will go beyond the bottom
        mediaRow=strict401gen.TR()
        mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan=str(len(thisRecord))))

    # add row to main table                
    mediaTable.append(mediaRow)
           
    return (mediaTable)

def mediaTable2(mediaData,cookieID,colWidths,config):
    # this function is not in use, experimental

    q="show columns from "+config['mediaTable']
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    colType=[]
    for thisCol in qresult:
        colType.append(thisCol[1])

    endWidth=32
    mediaTable=strict401gen.TableLite(border=0,CLASS='resultstable')
        
    rowcolor='#FFFF99'
    imageCount=0

    for thisRecord in mediaData:
                
        if rowcolor=='#FFFF99':
            rowcolor='#FFFFCC'
        else:
            rowcolor='#FFFF99'
            
        # check to see if it's an Item record
        q="select "+config['itemIDfield']+" from "+config['mediaTable']+\
        " where "+config['mediaIDfield']+'="'+str(thisRecord[0])+'"'
        
        qresult=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        if qresult[0]:
            mediaType="I"
        else:
            mediaType=""

        mediaRow=strict401gen.TR(style="background-color:"+rowcolor)
        
        # record the number of cols with values
        colValues=0
        for thisCol in thisRecord:
            if thisCol:
                colValues=colValues+1
        
        # display all non binary fields
        for thisCol in range(0,len(thisRecord)):
            
            if 'blob'not in colType[thisCol]:
                        
                if thisCol==0:
                    # column for the edit button if not a All search
                    edimage=strict401gen.Image(("images/edit.png",str(endWidth),str(endWidth)),alt="Edit",name="Edit",title="Edit Record")
                    mediaRow.append(strict401gen.TD(strict401gen.Href("index?medit="+mediaType+str(thisRecord[thisCol]),edimage),valign='top',colspan="1",Class="mediacol0"))
                                    
                    
                # if it's not an image, it's text
                elif thisRecord[thisCol]:
                
                    if colValues==3:
                        columns=1
                        colClass='mediacol1'
                    else:
                        columns=2
                        colClass='mediacol3'
                    
                    text1=str(thisRecord[thisCol])
                    text2=text1.replace('\r\n','<BR>')
                    text3=text2.replace('\n','<BR>')
                    text=strict401gen.RawText(text3.replace('\r','<BR>'))
                    mediaRow.append(strict401gen.TD(text,colspan="1",valign='top',Class=colClass))
                    
        # put any images at the end of the row
        for thisCol in range(0,len(thisRecord)):
            
            if 'blob'in colType[thisCol]:
                            
                # if this col is an image set the image type
                try:
                    imgType=imghdr.what('',thisRecord[thisCol])
                    # force 3 char extention for windows
                    if len(imgType)>3:
                        imgType=imgType[0:2]+imgType[-1:]
                    else:
                        imgType=imgType
                except:
                    # default image space holder
                    imgType=''
                    
                if imgType:
                    if os.path.exists(config['mediaPath']+cookieID):
                        pass
                    else:
                        os.mkdir(config['mediaPath']+cookieID)
                    imageCount=imageCount+1
                    #~ imagename=str(imageCount)+'.'+imgType
                    imagename=str(thisRecord)+'.'+imgType
                    imgFile=open(config['mediaPath']+cookieID+'/'+imagename,"wb")
                    imgFile.write(thisRecord[thisCol])
                    imgFile.close()
                    httpImage="tmp/"+cookieID+'/'+imagename
                else:
                    #~ httpImage="images/shim.gif"
                    httpImage=''
                                        
                if colValues==3:
                    columns=1
                    colClass='mediacol2'
                else:
                    columns=2
                    colClass='mediacol3'
                if httpImage:
                    imageLink=strict401gen.Href(httpImage,strict401gen.Image(httpImage,alt="alt.img",Class="mediaimage"),onClick="window.open(this.href);return false;")
                    mediaRow.append(strict401gen.TD(imageLink,colspan="1",valign='top',Class=colClass))
                else:
                    #~ imageLink=strict401gen.Href(httpImage,strict401gen.Image(httpImage,alt="alt.img",Class="mediaimage"),onClick="window.open(this.href);return false;")
                    mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="1",valign='top',Class="colClass"))

        # or else it's empty
        if colValues==1:
            mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2",Class="mediacol3"))
                    
        mediaTable.append(mediaRow)
        
        
        # last row first col
        mediaRow=strict401gen.TR()
        mediaRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",endWidth,"10"),alt="Edit")))
        # last row middle cols
        for thisCol in colWidths:
            mediaRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif",str(int(thisCol)),"10"),alt="Edit")))
        # last row last col
        mediaRow.append(strict401gen.TD(strict401gen.Image(("images/shim.gif","128","10"),alt="Edit")))
        
        # add a row to make sure the scroll will go beyond the bottom
        #~ mediaRow=strict401gen.TR()
        #~ mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan=str(len(thisRecord))))
                
    mediaTable.append(mediaRow)
           
        
    return (mediaTable)

def createMedia(mediaID,catID,item,config):
    
    cols=[]
    if mediaID[0]=='I':
        mediaID=mediaID[1:]
        mediaType='Imedia'
    else:
        mediaType='media'
    
    q="show columns from "+config['mediaTable']    
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

    mediaTable=strict401gen.TableLite(border=0,Class="edittable")
    
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
            mediaRow.append(strict401gen.TD(strict401gen.Select(enumList,name=thisField[0],Class="editfield")))
            
        elif 'set(' in thisField[1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],multiple=1,size=len(setList),Class="editfield")))                    
            
        elif 'text' in thisField[1]:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Textarea(name=thisField[0],Class="editfield dataInput")))
            
        elif 'blob' in thisField[1]:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type='file',name=thisField[0],size="10",Class="editfield")))
            
        elif 'date' in thisField[1]:
            x=string.strip(str(datetime.date.today()))
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=thisField[0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in thisField[1]:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],maxlength="6",Class="editfield dataInput")))

        elif 'float' in thisField[1]:
            maxlen=maxlen.split(',')[0]              
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],maxlength="6",Class="editfield dataInput")))

        else:
            mediaRow.append(strict401gen.TD(thisField[0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",name=thisField[0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            mediaTable.append(mediaRow)
            mediaRow=strict401gen.TR()
        elif count==len(cols):
            mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2"))
            mediaTable.append(mediaRow)

    if mediaType=='Imedia':
        # find the related item record
        q="select "+",".join(config['itemUniqueID'])+" from "+config['itemTable']+\
        " where "+config['itemIDfield']+"='"+str(item[1])+"'"
        
        info=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        caption='Insert '+config['mediaTable']+' for '+" ".join(info)+' '
    else:
        # for a category header
        q2='select '+config['catInfo']+' from '+\
        config['catTable']+' where '+ config['catIDfield']+'="'+str(catID)+'"'

        info=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
        #~ caption='Insert '+config['mediaTable']+' for '+info[0]
        caption='Insert '+config['mediaTable']+' for '+" ".join(info)+' '

    header=formbuttons('create')
    
    return (caption,header,mediaTable,mediaType)

def editMedia(mediaID,catID,item,config):

    cols=[]
    colNames=[]
    if mediaID[0]=='I':
        mediaID=mediaID[1:]
        mediaType='Imedia'
    else:
        mediaType='media'
        
    # get the column  names
    q="show columns from "+config['mediaTable']
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

    # get col values
    selectCols=string.join(colNames,",")
    q="select "+selectCols+" from "+config['mediaTable']+\
    " where "+config['mediaIDfield']+"='"+mediaID+"'"
    
    values=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

    mediaTable=strict401gen.TableLite(border="0",Class="edittable")
    
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
            mediaRow.append(strict401gen.TD(strict401gen.Select(enumList,selected=values[0][thisField],name=cols[thisField][0],Class="editfield")))
            
        elif 'set(' in cols[thisField][1]:
            setList=thisField[1].split(",")
            setList[0]=setList[0][5:]
            setList[len(setList)-1]=setList[len(setList)-1][:-1]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Select(setList,name=thisField[0],multiple=1,size=len(setList),Class="editfield")))                    
        
        elif 'text' in cols[thisField][1]:
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Textarea(values[0][thisField],name=cols[thisField][0],rows='10',cols='50',Class="editfield dataInput")))
            
        elif 'blob' in cols[thisField][1]:
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type='file',name=cols[thisField][0],Class="editfield",size="10"),Class="editfield"))
        
        elif 'date' in cols[thisField][1]:
            if not values[0][thisField] or values[0][thisField]=="None":
                x=string.strip(str(datetime.date.today()))
            else:
                x=values[0][thisField]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=x,name=cols[thisField][0],maxlength="10",Class="editfield dataInput")))

        elif 'int' in cols[thisField][1]:
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        elif 'float' in cols[thisField][1]:
            maxlen=maxlen.split(',')[0]
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength="6",Class="editfield dataInput")))

        else: # char fields
            mediaRow.append(strict401gen.TD(cols[thisField][0],Class="editlabel"))
            mediaRow.append(strict401gen.TD(strict401gen.Input(type="text",value=values[0][thisField],name=cols[thisField][0],maxlength=maxlen,Class="editfield dataInput")))

        if not count%2:
            mediaTable.append(mediaRow)
            mediaRow=strict401gen.TR()
        elif count==len(cols):
            mediaRow.append(strict401gen.TD(strict401gen.RawText("&nbsp"),colspan="2"))
            mediaTable.append(mediaRow)
            
    if mediaType=='Imedia':
        # find the related item record
        q="select "+",".join(config['itemUniqueID'])+" from "+config['itemTable']+\
        " where "+config['itemIDfield']+"='"+str(item[1])+"'"
        
        info=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        caption='Insert '+config['mediaTable']+' for '+" ".join(info)+' '
    else:
        # find the related cat record
        q="select "+config['catIDfield']+" from "+config['mediaTable']+\
        " where "+config['mediaIDfield']+"='"+mediaID+"'"
        
        value=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
        catID=value[0]

        # for a category header
        q2='select '+config['catInfo']+' from '+\
        config['catTable']+' where '+ config['catIDfield']+'="'+str(catID)+'"'

        info=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
        caption='Update '+config['mediaTable']+' for '+info[0]
        
    header=formbuttons('update')

    return(caption,header,mediaTable,mediaType,catID)

############ support functions

def relatedRecords(itemID,config):
    
    # see if there is at least one record in the cat table related to the current item
    # return a 1 if there is, a zero if not
    records=[]
    q="SELECT * FROM "+config['catTable']+" where "+config['catTable']+"."+config['itemIDfield']+"='"+str(itemID)+"'"
    r=db.dbConnect(config['selectedHost'],config['dbname'],q,1)
    if r:
        records.append(r)
    related=str(len(records))
    
    return related

def cleanTmp(config):
    
    # delete the tmp files whenever itemQuery or catQuery are called
    
    subDirs=os.listdir(config['mediaPath'])
    for dir in subDirs:
        if dir[0]!=".":
            shutil.rmtree(config['mediaPath']+dir)
        
    return

def lastUpdate(config):
    
    q='select '+\
    config['mediaTable']+'.'+config['catIDfield']+','+\
    config['mediaTable']+'.'+'modstamp '+\
    'from '+config['mediaTable']+\
    ' order by '+config['mediaTable']+'.'+'modstamp '+'desc'
    
    qresult1=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    record=0
    while not qresult1[record][0]:
        record=record+1
    else:
        catID=str(qresult1[record][0])
    
    q2="select "+\
    config['catTable']+'.'+config['itemIDfield']+\
    ' from '+config['catTable']+\
    ' where '+config['catTable']+'.'+config['catIDfield']+'="'+catID+'"'
    
    qresult=db.dbConnect(config['selectedHost'],config['dbname'],q2,1)
    itemID= str(qresult[0])
    
    return (itemID,catID)
    
def formbuttons(which):
    

    if which=='update':
        saveButton=strict401gen.Input(type="image",name="updatebutton",srcImage="images/UPDATE2.png",alt="UPDATE",title="Update this Record",Class="savebutton")
        cancelButton=strict401gen.Input(type="image",name="cancelbutton",srcImage="images/CANCEL2.png",alt="CANCEL",title="Cancel Edit",Class="cancelbutton")

    elif which=='create':
        saveButton=strict401gen.Input(type="image",name="savebutton",srcImage="images/SAVE2.png",alt="SAVE",title="Save this Record",Class="savebutton")
        cancelButton=strict401gen.Input(type="image",name="cancelbutton",srcImage="images/CANCEL2.png",alt="CANCEL",title="Cancel Edit",Class="cancelbutton")

    elif which=='item':
        saveButton=strict401gen.Input(type="image",name="savebutton",srcImage="images/notes.png",alt="SAVE",title="Save this Record",Class="savebutton")
        cancelButton=strict401gen.Input(type="image",name="cancelbutton",srcImage="images/edit3.png",alt="CANCEL",title="Cancel Edit",Class="cancelbutton")

    
    return [saveButton,cancelButton]
    
def getCatColWidths(header, config):
    
    colLengths=[]
    minColLen=7
    maxColLen=18
    dateLen=10
    tableWidth=725
    
    # column lengths for the item table
    q="show columns from "+config['itemTable']
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    # special case, combo item/cat header
    if header[0]==config['itemTable'].upper():
        colLen=0
        for thisCol in colInfo:
            if thisCol[0] in config['itemUniqueID']:
                colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
                colLen=colLen+int(colLength)
        if colLen<minColLen:
            colLen=minColLen
        if colLen>maxColLen:
            colLen=maxColLen
    
        colLengths.append(colLen)            
            
    # column lengths for the catTable
    q="show columns from "+config['catTable']
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
    q="show columns from "+config['itemTable']
    colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
    
    
    # special case search, combo item/cat header
    if header[0]==config['itemTable'].upper():
        colLen=0
        for thisCol in colInfo:
            if thisCol[0] in config['itemUniqueID']:
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
    q="show columns from "+config['mediaTable']
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

def updateCookie(req,name,value,config):
    
    data=kooky2.myCookies(req,'get','',config['dbname'],config['selectedHost'])
    data[name]=value
    kooky2.myCookies(req,'save',data,config['dbname'],config['selectedHost'])
    
    return



############ about functions

def aboutInfo(config):
    
    caption="About "+config['dbname']
    header=""
    result=[\
    ["Author: Gary M Witscher"],
    ["Date: 2009-08-08"],
    ["Version: 1.2"],
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

    resultTable=strict401gen.TableLite(border="0",CLASS='resultstable')
    rowcolor='#FFFFBA'
    aboutIntro="font:10pt Tahoma, serif;text-align:center;"
    
    for thisRow in aboutData:
        # indicates a title line
        if thisRow[0][0]=="-":
            if rowcolor=='#FFFFBA':
                rowcolor='#FFFFCC'
            else:
                rowcolor='#FFFFBA'
            rRow=strict401gen.TR(style="background-color:"+rowcolor)
            rRow.append(strict401gen.TD(thisRow[0][1:],style="width:785px;font: 14pt Times, serif, bold;text-align:center;"))
            aboutIntro="font:10pt Arial, sans;text-align:left;"
        # not a title, just a data line
        else:
            rRow=strict401gen.TR(style=aboutIntro+"background-color:"+rowcolor)
            rRow.append(strict401gen.TD(thisRow[0],style="width:785px;"))

        resultTable.append(rRow)
        
    if rowcolor=='#FFFFBA':
        rowcolor='#FFFFCC'
    else:
        rowcolor='#FFFFBA'
        
    rRow=strict401gen.TR(style="background-color:"+rowcolor)
    rRow.append(strict401gen.TD(strict401gen.RawText("&nbsp;"),style="width:785px;"))
    resultTable.append(rRow)

    return (resultTable)
    
def editConfig(req,config):

    configTable=strict401gen.TableLite(border=0,Class="edittable")
    
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
    rowcolor='#ffe2aa'#FFFFBA'
    
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
                configRow.append(strict401gen.TD(descText,colspan="1",Class="editlabel",style="background-color:"+rowcolor))
                passInput=0
                descText=""

                if rowcolor=='#FFFFBA':
                    rowcolor='#ffe2aa'#FFFFCC'
                else:
                    rowcolor='#FFFFBA'
                
        elif "#" not in lines[thisLine] and "=" in lines[thisLine] and passInput==0:
            configData=lines[thisLine].split("=")
            configName=configData[0]
            configValue=configData[1]
            configRow.append(strict401gen.TD(strict401gen.Input(type="text",value=configValue,name=configName,size=maxsize,maxlength=maxlen,Class="editfield dataInput"),colspan="1"))
            
            configTable.append(configRow)

        
    caption='Edit configuration.'
    header=formbuttons('update')
    
    return (caption,header,configTable,'writeConfig')

def createConfig(req,config):

    configTable=strict401gen.TableLite(border=0,Class="edittable")
    
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
    rowcolor='#ffe2aa'#FFFFBA'
    
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
                configRow.append(strict401gen.TD(descText,colspan="1",Class="editlabel",style="background-color:"+rowcolor))
                passInput=0
                descText=""

                if rowcolor=='#FFFFBA':
                    rowcolor='#ffe2aa'#FFFFCC'
                else:
                    rowcolor='#FFFFBA'
                
        elif "#" not in lines[thisLine] and "=" in lines[thisLine] and passInput==0:
            configData=lines[thisLine].split("=")
            configName=configData[0]
            configValue=''
            configRow.append(strict401gen.TD(strict401gen.Input(type="text",value=configValue,name=configName,size=maxsize,maxlength=maxlen,Class="editfield dataInput"),colspan="1"))
            
            configTable.append(configRow)

        
    caption='Create configuration.'
    header=formbuttons('create')
    
    return (caption,header,configTable,'writeConfig')

