function addNew(text){
    var h = document.createElement("div");
    //var t = document.createTextNode(text);
    h.innerHTML += text;
    h.style.width = "5em";
    h.style.height = "2em";
    h.style.border = "1px solid black";
    h.style.textAlign = "center";
    h.style.marginBottom = "1px";

    var page = document.createElement("html");
    document.body.appendChild(page);

    document.body.appendChild(h);
}

function promptFunction(){
    var x;
    var name=prompt("Please enter a folder name","Folder name");
    if (name!=null){
      var x = addNew(name);
    }
}