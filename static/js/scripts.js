let listName = document.getElementById('list-name')
let boxes = document.getElementsByClassName('new-checkbox').length;


function save() {
  let checkedBoxes = 0;
  for(let i = 1; i <= boxes; i++){
	var checkbox = document.getElementById(String(i));
    localStorage.setItem(`${listName.innerHTML}` + String(i), checkbox.checked);
    if (checkbox.checked){
        checkedBoxes++;
        console.log(checkbox.checked);
        console.log(checkedBoxes);
    };
  }
  localStorage.setItem(`${listName.innerHTML}`, String(checkedBoxes));
  localStorage.setItem(`${listName.innerHTML}-tasks`, String(boxes));
  progressBar();
}



//for loading
for(let i = 1; i <= boxes; i++){
  if(localStorage.length > 0){
    var checked = JSON.parse(localStorage.getItem(`${listName.innerHTML}` + String(i)));
    document.getElementById(String(i)).checked = checked;
  }
}
window.addEventListener('change', save);

function progressBar () {
    let listProgressArray = [...document.getElementsByClassName('list-progress')]
    for (let i = 0; i < listProgressArray.length; i++) {
        var progress = (localStorage.getItem(`${listProgressArray[i].id}`));
        var total = (localStorage.getItem(`${listProgressArray[i].id}-tasks`));
        var percentage = ((progress/total)*100).toFixed(0);
        document.getElementById(listProgressArray[i].id).innerHTML = `
            <progress class="progress-bar" value="${progress}" max="${total}"></progress>
            <label class="progress-text">${percentage === "NaN"? 0 : percentage}%</label>`;
    }
}

progressBar();

//window.onload = function(){
//    var le = document.querySelectorAll('input[name="chkboxes[]"]:checked').length;;
//    var lengthOfName = name.length
//
//    document.getElementById('output').innerHTML = lengthOfName;
//};
