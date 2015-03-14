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
function showchapter(ac,c){
for(i=1;i<=c;i++){
	document.getElementById('tc'+i).style.display = 'none';
	document.getElementById('L'+i).style.color = ''; 
	document.getElementById('chapterImg'+i).src = './images/chapter-blank.png'; 
}
document.getElementById('tc'+ac).style.display = 'inline-block';
document.getElementById('L'+ac).style.color = '#000000'; 
document.getElementById('chapterImg'+ac).src = './images/chapter-active10.png'; 
}

//n = number of hidden pages
function showpage(a,n){
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
