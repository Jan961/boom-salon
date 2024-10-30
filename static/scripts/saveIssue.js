var csrf = document.getElementsByName('csrfmiddlewaretoken');
var buttons = document.getElementsByClassName('favourite');

for (const iss of savedIss) {
    saved(iss, 1);
}

function saveIssue() {
    const issueName = event.target.value;

    $.ajax({
        type: 'post',
        url: '/saveissue/',
        data: {
            'csrfmiddlewaretoken': csrf[0].value,
            'name': issueName,
        },
        dataType: 'json',
        success: function(response) {
            saved(issueName, response.value);
        },
        error: function(error) {
            console.log(error);
            alert('Oops, something went wrong!');
        }
    })
}

function saved(issueName, value) {
    for (button of buttons) {
        if (button.value === issueName) {
            if (value === 0) {
                button.classList.remove('selected');
                button.innerHTML = "Add to My Magazines"
                button.style.backgroundColor ="#E8E5E2";
            } else {
                button.classList.add('selected');
                button.innerHTML = "Remove from My Magazines"
                button.style.backgroundColor = "lightgrey";
            }
        }
    }
}