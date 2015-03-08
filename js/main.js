function mainPlusArrow(theChoice){
    mainPlusImage=new Array("images/down2.png","images/down3.png")
    document.getElementById("mainArrowPlus").src= mainPlusImage[theChoice]
}

function mainMinusArrow(theChoice){
    mainMinusImage=new Array("images/up2.png","images/up3.png")
    document.getElementById("mainArrowMinus").src= mainMinusImage[theChoice]
}

function mainSrc(){
    top.document.getElementById("resultFrame").src="mainResult.html"
}

//function setFocus()
//{
//document.getElementById('dogleg').style.backgroundColor="#FFFF99"
//document.getElementById('dogleg').focus()
//}

//c=number of chapters
function showc(ac,c){
for(i=1;i<=c;i++){
	document.getElementById('tc'+i).style.display = 'none';
//	document.getElementById('c'+i).style.background = ''; 
}
document.getElementById('tc'+ac).style.display = 'inline-block';
//document.getElementById('c'+ac).style.background = '#a39797'; 
}

//n = number of hidden pages
function showp(a,n){
if (document.getElementById('t'+a).style.display == 'inline-block') {
	document.getElementById('t'+a).style.display = 'none';
	document.getElementById('triangle'+a).src = './images/docright.png';
}else {
	for(i=1;i<=n;i++){
		document.getElementById('t'+i).style.display = 'none';
		document.getElementById('triangle'+i).src = './images/docright.png'; 
	}
	document.getElementById('t'+a).style.display = 'inline-block';
	document.getElementById('triangle'+a).src = './images/docdown.png';
}
}
