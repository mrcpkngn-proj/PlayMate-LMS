document.addEventListener("DOMContentLoaded", () => {

    const progressBar = document.getElementById("quiz-progress-bar");
    const progressContainer = document.querySelector(".quiz-progress");
    const rocket = document.getElementById("rocket-icon");

    if (!progressBar || !progressContainer || !rocket)
        return;

    //--------------------------------------------------
    // Position rocket
    //--------------------------------------------------

    function getRocketLeft(percent) {

        const containerWidth =
            progressContainer.clientWidth;

        const rocketWidth =
            rocket.offsetWidth;

        let left =
            (containerWidth * (percent / 100))
            - rocketWidth / 2;

        left = Math.max(
            0,
            Math.min(
                left,
                containerWidth - rocketWidth
            )
        );

        return left;

    }

    function moveRocket(percent, animate = true) {

        if (!animate) {
            rocket.style.transition = "none";
            progressBar.style.transition = "none";
        } else {
            rocket.style.transition = "left .45s ease";
            progressBar.style.transition = "width .45s ease";
        }

        progressBar.style.width = percent + "%";
        rocket.style.left = getRocketLeft(percent) + "px";

        if (!animate) {

            // Force repaint

            rocket.offsetHeight;

            rocket.style.transition = "left .45s ease";
            progressBar.style.transition = "width .45s ease";
        }
    }

    function advanceToNextQuestion(form) {

        const nextPercent = Math.min(
            progress + (100 / totalQuestions),
            100
        );

        moveRocket(nextPercent);

        setTimeout(() => {

            HTMLFormElement.prototype.submit.call(form);

        }, 500);

    }

    window.advanceToNextQuestion =
        advanceToNextQuestion;

    window.moveQuizRocket = moveRocket;

    //--------------------------------------------------
    // Initial placement
    //--------------------------------------------------

    if (typeof progress !== "undefined") {
        moveRocket(progress, false);
    }

    //--------------------------------------------------
    // Single-page quiz
    //--------------------------------------------------

    if (typeof progress === "undefined") {

        function updateProgress() {

            let answered = 0;

            document.querySelectorAll(".question-card").forEach(card => {

                if (card.querySelector("input:checked"))
                    answered++;

            });

            moveRocket(answered / totalQuestions * 100);

        }

        document.addEventListener("change", updateProgress);
        window.addEventListener("resize", updateProgress);

        updateProgress();

        return;
    }

    //--------------------------------------------------
    // Per-question quiz
    //--------------------------------------------------

    const nextButton = document.getElementById("next-button");
    const form = document.getElementById("question-form");

    if (nextButton && form) {

        nextButton.addEventListener("click", function(e){

            e.preventDefault();

            const selected =
                form.querySelector(
                    'input[name="choice"]:checked'
                );

            if (!selected) {

                alert("Please select an answer.");

                return;

            }

            nextButton.disabled = true;

            window.advanceToNextQuestion(form);

        });

    }
});