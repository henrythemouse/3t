# testvalue

def testvalue(req):
    try:
        x=req.form['test']
    except:
        x="No length to testValue"
    
    req.content_type="text/html;charset=UTF-8"
    req.write("testvalue: "+str(x))
    