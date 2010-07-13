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
