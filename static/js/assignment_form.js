document.addEventListener("DOMContentLoaded", () => {

    const container = document.getElementById("attachment-container");

    const template = document.getElementById("attachment-template");

    const addButton = document.getElementById("add-attachment");

    const dropZone = document.getElementById("drop-zone");

    function createAttachmentRow(file=null) {

        const clone = template.content.cloneNode(true);

        const input = clone.querySelector(".attachment-input");

        const dataTransfer = new DataTransfer();

        const filename = clone.querySelector(".attachment-filename");

        input.addEventListener("change", function () {


            if (this.files.length > 0) {

                filename.textContent =
                    "📄 " + this.files[0].name;

            }
            else {

                filename.textContent =
                    "No file selected";

            }

        });
        if(file){

            dataTransfer.items.add(file);

            input.files = dataTransfer.files;

            filename.textContent =
                "📄 " + file.name;

        }

        container.appendChild(clone);

    }

    addButton.addEventListener("click", () => {

        createAttachmentRow();

    });


    container.addEventListener("click", function (event) {

        if (!event.target.classList.contains("remove-attachment"))
            return;

        event.target
            .closest(".attachment-input-row")
            .remove();

    });




    /* ==========================
    Delete Attachment Modal
    ========================== */

    const modal =
        document.getElementById("deleteAttachmentModal");

    const deleteText =
        document.getElementById("attachmentDeleteText");

    const confirmDelete =
        document.getElementById("confirmDelete");

    document.querySelectorAll(".open-delete-modal")
    .forEach(button => {

        button.addEventListener("click", () => {

            deleteText.textContent =
                `Are you sure you want to delete "${button.dataset.name}"?`;

            confirmDelete.href =
                button.dataset.url;

            modal.classList.remove("hidden");

        });

    });

    document
    .getElementById("cancelDelete")
    .addEventListener("click", () => {

        modal.classList.add("hidden");

    });

    window.addEventListener("click", e => {

        if (e.target === modal)
            modal.classList.add("hidden");

    });

    dropZone.addEventListener("dragover", e => {

        e.preventDefault();

        dropZone.classList.add("dragging");

    });

    dropZone.addEventListener("dragleave", () => {

        dropZone.classList.remove("dragging");

    });

    dropZone.addEventListener("drop", function(e){

        e.preventDefault();

        dropZone.classList.remove("dragging");

        const files = e.dataTransfer.files;

        for(let file of files){

            createAttachmentRow(file);

        }

    });

});