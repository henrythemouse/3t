import db


config={'globalSearchFields': ['title_', 'subtitle', 'kind', 'date'], 'displaynamelocation': 'top', 'catField': 'kind', 'itemIMGfield': 'img', 'itemUniqueID': ['firstname_', 'lastname_'], 'catInfo': 'title_', 'displaylogo': 'read.jpg', 'catIDfield': '_read', 'mediaTable': 'note', 'catTable': 'readit', 'mediaPath': '/var/www/3t/tmp/', 'configFile': '/var/www/3t/conf/config-read.txt', 'configError': 'no', 'selectedHost': 'localhost', 'displayname': 'READ', 'dbname': 'read', 'catImagePath': '/var/www/3t/catimages/', 'itemIDfield': '_author', 'itemImagePath': '/var/www/3t/itemimages/', 'mediaIDfield': '_nid', 'orderbyField': 'date', 'itemTable': 'author'}

header=['FIRSTNAME_', 'LASTNAME_', 'OTHERNAME', 'URL', 'DATE']




colLengths=[]
minColLen=10
maxColLen=25
dateLen=10
tableWidth=725

#~ # column lengths for the item table
#~ q="show columns from "+config['itemTable']
#~ colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)
colInfo=(('firstname_', 'varchar(25)', 'YES', 'MUL', None, ''), ('lastname_', 'varchar(25)', 'YES', '', None, ''), ('othername', 'varchar(25)', 'YES', '', None, ''), ('url', 'varchar(100)', 'YES', '', None, ''), ('_author', 'int(4) unsigned zerofill', 'NO', 'PRI', None, 'auto_increment'), ('modstamp', 'timestamp', 'NO', '', 'CURRENT_TIMESTAMP', ''), ('createDate', 'date', 'YES', '', None, ''), ('img', 'blob', 'YES', '', None, ''))


# special case for global search, combo item/cat header
if header[0]==config['itemTable'].upper():
    colLen=0
    for thisCol in colInfo:
        if thisCol[0] in config['itemUniqueID']:
            colLength=thisCol[1][thisCol[1].index("(")+1:thisCol[1].index(")")]
            colLen=colLen+int(colLength)
    if colLen>maxColLen:
        colLengths.append(maxColLen)
    else:
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
                        
                elif thisCol[0][0]!='_':
                
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

print repr(colLengths)

# column lengths for the catTable
#~ q="show columns from "+config['catTable']
#~ colInfo=db.dbConnect(config['selectedHost'],config['dbname'],q,0)

colInfo=(('_read', 'int(4) unsigned zerofill', 'NO', 'PRI', None, 'auto_increment'), ('_author', 'int(10) unsigned', 'YES', '', '0', ''), ('title_', 'varchar(100)', 'YES', 'MUL', None, ''), ('subtitle', 'varchar(100)', 'YES', '', None, ''), ('source', 'varchar(25)', 'YES', '', 'SDCL', ''), ('kind', "enum('Science_Fiction','Mystery','Native_American','Science_Nonfiction','General_Fiction','General_Nonfiction','To_Read')", 'NO', '', 'Science_Fiction', ''), ('date', 'date', 'YES', '', None, ''), ('modstamp', 'timestamp', 'NO', '', 'CURRENT_TIMESTAMP', ''))

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
                    
            elif '_' not in thisCol[0][0]:
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

print repr(colWidths)
