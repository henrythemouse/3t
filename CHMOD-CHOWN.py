#! /usr/bin/python

# either run this as root (sudo) or be a member of the chownGroup
# it will chmod/chown dirs that need to be apache writable

import os
import os.path
import stat

# set the list of dirs and user/group
writeableDirs=['catimages','images','itemimages','tmp','conf']
chownUser=1000
chownGroup=33
chmodInt=stat.S_IRWXU|stat.S_IRWXG   ##0770

currentDir=os.getcwd()
print
print 'the current directory: '+currentDir
print
dirList=os.listdir(currentDir)

for thisFile in dirList:
	if os.path.isdir(thisFile):
		thisDir=thisFile
		print '.'
		if thisDir in writeableDirs:
			print '-----------'
			print 'writeableDir found: '+thisDir
			print 'chown: '+str(chownUser)+','+str(chownGroup)
			print 'chmod: '+str(oct(chmodInt))

			os.chown(thisDir,chownUser,chownGroup)
			os.chmod(thisDir,chmodInt)
