var titles = document.getElementsByClassName('mag-title');
var infoBox = document.getElementById('mainbox');


for (const title of titles) {
    var magId = window.location.pathname.split("/");

    if (title.id  === magId[1]) {
        title.classList.add("yellow");
    }
}
