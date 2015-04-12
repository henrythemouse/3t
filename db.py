# Connect

import MySQLdb
import string


def dbConnect(selectedHost,dbToOpen,queryText,fetchFlag):

    # use these as defaults
    # this function is only used for select statements
    # the default user should only have select privileges (except with the system tables)
    
    hostUser=dbToOpen
    hostPw=dbToOpen

    queryResult=0


    dbConnection=MySQLdb.connect(host=selectedHost,user=hostUser,passwd=hostPw,db=dbToOpen)
    dbCursor=dbConnection.cursor()
    #~ dbCursor.execute(queryText)

    try:
        # the following while breaks cookie inserts - BROKEN
        #~ while queryText.find('\\x')!=-1:
            #~ hexLoc = queryText.find('\\x')
            #~ hexChars = queryText[hexLoc : (hexLoc+4)]
            #~ intChars = '0x'+ hexChars[2:]
            #~ queryText=queryText.replace(hexChars, chr(int(intChars,16)))

        dbCursor.execute(queryText)
    except:
        queryResult=queryResult+(-4)

    # don't want to return results - example might be an insert/update query
    #
    if fetchFlag==-1:
#         queryResult=dbCursor.fetchall()
        queryResult=str(queryResult)+"===="+str(queryText)

    # looking for the all results of a selection query
    elif fetchFlag==0:
        try:
            queryResult=dbCursor.fetchall()
        except:
            queryResult=queryResult+(-8)
    # looking for ONE result from a selection query
    elif fetchFlag==1:
        try:
            queryResult=dbCursor.fetchone()
        except:
            ## pass
            queryResult=queryResult+(-100)

    #~ if fetchFlag==0:
        #~ queryResult=dbCursor.fetchall()
    #~ elif fetchFlag==1:
        #~ queryResult=dbCursor.fetchone()
    #~ else:
        #~ queryResult=0

    # *************************************************************
    # close the connection for each query
    # I don't want open connections hanging around
    #
    try:
        dbCursor.close()
    except:
        pass
    try:
        # for transactional tables like innodb
        dbConnection.commit()
    except:
        pass    
    try:
        dbConnection.close()
    except:
        pass

#    queryResult=-12

    return queryResult