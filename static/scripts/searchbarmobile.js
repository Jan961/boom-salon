
function checkMatching( listOfWordsToCheck, inputText ){

    for(k = 0; k < listOfWordsToCheck.length; k++ ){
        if (listOfWordsToCheck[k].toUpperCase().indexOf(inputText) > -1 ){
            return true;
        }
    }
    return false;

}

function addHashtagsToTheList ( hashtags, listOfWordsToCheck){

    for (j = 0; j <hashtags.length; j++ ) {
        var hashtagText = hashtags[j].textContent ||
                            hashtags[j].innerText;
        listOfWordsToCheck.push(hashtagText);
        }
}



function searchBarFunction(){
    var searchBarInput = document.getElementById("searchBar")
    var filter = searchBarInput.value.toUpperCase();

    var magList = document.getElementsByClassName("mag_list_element_wrap")

    for (i = 0; i < magList.length; i++) {
        const listOfWordsToCheck = [];
        var title = magList[i].getElementsByTagName("span")[0].textContent ||
                    magList[i].getElementsByTagName("span")[0].innerText;
        listOfWordsToCheck[listOfWordsToCheck.length] = title;

        var hashtags = magList[i].getElementsByTagName("hashtag")
        addHashtagsToTheList(hashtags, listOfWordsToCheck );


        if (checkMatching(listOfWordsToCheck,filter ))
        {
            magList[i].style.display = "block";
        }
        else {
            magList[i].style.display = "none";
        }
    }

}