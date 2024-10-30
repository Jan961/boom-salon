var acc = document.getElementsByClassName("menuelement");
var membinfo = document.getElementById("membershipinfo")
var openedElement = null;

membinfo.style.maxHeight = membinfo.scrollHeight + 'px';
var i;

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var thisPanel = this.nextElementSibling;
    var closeicon = this.lastElementChild;

    if (openedElement == this) {// clicking on the menu element whose hidden panel is open

      thisPanel.style.maxHeight = null;
      membinfo.style.maxHeight = membinfo.scrollHeight + 'px';
      openedElement = null;
      closeicon.style.opacity = "0%";
    }

    else if (openedElement) {// clicking on some menu element while another element has its hidden panel open

        var openedPanel = openedElement.nextElementSibling;
        var visiblecloseicon = openedElement.lastElementChild;
        visiblecloseicon.style.opacity = "0%";
        openedPanel.style.maxHeight = null;
        thisPanel.style.maxHeight = thisPanel.scrollHeight + "px";
        closeicon.style.opacity = "100%";
        openedElement = this;
    }

    else {//none of the hidden panels are open and therefore Membinfo is visible

        thisPanel.style.maxHeight = thisPanel.scrollHeight + "px";
        membinfo.style.maxHeight = 0;
        closeicon.style.opacity = "100%";
        openedElement = this;
    }
  });
}