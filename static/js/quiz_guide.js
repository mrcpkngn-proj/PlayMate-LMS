document.addEventListener("DOMContentLoaded", function () {

const openButton = document.getElementById("open-quiz-guide");
const closeButton = document.getElementById("close-quiz-guide");
const footerCloseButton = document.getElementById("close-quiz-guide-footer");
const modal = document.getElementById("quiz-guide-modal");

if (!openButton || !modal) {
    return;
}


// ================================
// OPEN GUIDE
// ================================

function openGuide() {

    modal.classList.add("active");

    modal.setAttribute("aria-hidden", "false");

    document.body.classList.add("quiz-guide-open");

}


// ================================
// CLOSE GUIDE
// ================================

function closeGuide() {

    modal.classList.remove("active");

    modal.setAttribute("aria-hidden", "true");

    document.body.classList.remove("quiz-guide-open");

}


// ================================
// BUTTON EVENTS
// ================================

openButton.addEventListener("click", openGuide);


if (closeButton) {

    closeButton.addEventListener("click", closeGuide);

}


if (footerCloseButton) {

    footerCloseButton.addEventListener("click", closeGuide);

}


// ================================
// CLICK OUTSIDE MODAL
// ================================

modal.addEventListener("click", function (event) {

    if (event.target === modal) {

        closeGuide();

    }

});


// ================================
// ESCAPE KEY
// ================================

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape" &&
        modal.classList.contains("active")) {

        closeGuide();

    }

});

});
