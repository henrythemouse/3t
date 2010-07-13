/*
-------------------------------------------------------------------

INSTRUCTIONS - Read Before Using Script

If you are using frames, the code referred to in steps 2 - 5 must be put in the 
pages displayed in the frames and NOT in the parent document.

Step 1
In the Usernames & Passwords section, configure the variables as
indicated by the comments.
 
Step 2:
Add the following code to the <head> section of your login page: 
 <script src="scripts/login.js"></script> 
Change "scripts/login.js" to reflect the correct path to this script
file on your server. 
 
Step 3:
Add this code to the login page, at the place you want the login
panel to show:
 
 <script language="JavaScript">
  BuildPanel();
 </script>
 
Step 4:
Add the following code to the <head> section of each page procteded
by this script:
 
 <script src="scripts/login.js"></script>
 <script language="JavaScript">
  checkCookie();
 </script>

Change "scripts/login.js" to reflect the correct path to the script
file on your server.
 
Step 5: 
On the page that is to have the logout button, paste this code where you
want the button to be:

 <form action="" name="frmLogoff">
  <input type="button" name="btLogoff" value="log out" onclick="logout();">
 </form>
 
 To use your own image instead of the grey button change the type from button to image
 and add src="myimage.gif" where myimage.gif is the image (including the path to it if
 needed, you want to use.
 
Step 6:
Upload this script and your html pages to the relevant directories
on your server. 




*/

//----------------------------------------------------------------
//  Usernames, Passwords & User Pages - These require configuration.
//----------------------------------------------------------------
var successpage = "index.py"; // The page users go to after login, if they have no personal page.
var loginpage = "index.py"; //Change this to the page the login panel is on.

var imgSubmit = ""; //Change to the path to your login image,if you don't want the standard button, otherwise do not change.
var imgReset = "";  //Change to the path to your reset image,if you don't want the standard button, otherwise do not change.

var users = new Array();

users[0] = new Array("username1","password1","member1.html"); // Change these two entries to valid logins.
users[1] = new Array("username2","password2","member2.html"); // Add addtional logins, straight after these, as
                                                           	  // required, followig the same format. Increment the 
											                  // numbers in the square brackets, in new each one. Note:
											                  // the 3rd parameter is the the page that user goes to
											                  // after successful login. Ensure the paths are correct.
                                                              // Make this "" if user has no personal page.
//----------------------------------------------------------------
//  Login Functions
//----------------------------------------------------------------
function login(username,password){
 var member = null;
 var loggedin = 0;
 var members = users.length;
 for(x=0;x<members && !loggedin; x++){
 if((username==users[x][0])&&(password==users[x][1])){
    loggedin = 1;
    member = x;
	break;
   }
 } 
 
 if(loggedin==1){
  if(users[member][2] != "") {
   successpage = users[member][2];
  }
  setCookie("login",1);
  if (top.location.href != location.href){
   location.href = successpage;           
  }else{
   top.location.href = successpage;  
  }
 }else{
  alert('access denied'); // Insert a fail message.
 }  
}

function logout() {
 deleteCookie("login");
 if (top.location.href != location.href){
  location.href = loginpage;           
 }else{
  top.location.href = loginpage;  
 }
}

//----------------------------------------------------------------
// Cookie Handler
//----------------------------------------------------------------
var ckTemp = document.cookie;

function setCookie(name, value) { 
 if (value != null && value != "")
  document.cookie=name + "=" + escape(value) + ";";
 ckTemp = document.cookie;
 }
 
function deleteCookie(name) {
  if (getCookie(name)) {
    document.cookie = name + "=" +
    "; expires=Thu, 01-Jan-70 00:00:01 GMT";
  }
}

function getCookie(name) { 
 var index = ckTemp.indexOf(name + "=");
 if(index == -1) return null;
  index = ckTemp.indexOf("=", index) + 1;
 var endstr = ckTemp.indexOf(";", index);
 if (endstr == -1) endstr = ckTemp.length;
 return unescape(ckTemp.substring(index, endstr));
 }
  
function checkCookie() {
 var temp = getCookie("login");
 if(!temp==1) {
  alert('access denied'); // Rensert a fail message.
  if(top.location.href != location.href){
   location.href = loginpage;           
  }else{
   top.location.href = loginpage;  
  }
 }
}

//----------------------------------------------------------------
// Login Panel
//----------------------------------------------------------------

function BuildPanel() {
document.write('<form name="logon"><table align="left" border="0"><tr><td align="right">');
document.write('<small><font face="Verdana">Username:</font></small></td>');
document.write('<td><small><font face="Verdana"><input type="text" name="username" size="20"></font></small></td></tr>');
document.write('<tr><td align="right"><small><font face="Verdana">Password:</font></small></td>');
document.write('<td><small><font face="Verdana"><input type="password" name="password" size="20"></font></small></td></tr>');
if(imgSubmit == ""){
 document.write('<tr><td align="center" colspan="2"><p><input type="button" value="Logon" name="Logon" onclick="login(username.value,password.value)">'); 
} else {
 document.write('<tr><td align="center" colspan="2"><p><input type="image" src="'+imgSubmit+'" name="Logon" onclick="login(username.value,password.value)">');
}
if(imgReset == ""){
 document.write('<input type="reset" value="Reset" name="Reset">');
} else {
 document.write('<input type="image" src="'+imgReset+'" name="Reset" onclick="logon.reset();">');
}
document.write('</p></td></tr></table></form>');
}

