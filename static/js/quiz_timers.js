console.log("quiz_timers.js loaded!");

function startQuizTimer() {
    const timerElement = document.getElementById("quiz-timer");
    if (!timerElement) return;

    const startedAt = new Date(timerElement.dataset.startedAt);
    const durationMinutes = parseInt(timerElement.dataset.duration, 10);
    const endTime = new Date(startedAt.getTime() + durationMinutes * 60000);

    function updateTimer() {
        const now = new Date();
        const diff = endTime - now;

        if (diff <= 0) {
            timerElement.textContent = "Time's up!";
            const form =
            document.getElementById("question-form")
            ||
            document.getElementById("quiz-form");
            if (form) form.submit();
        } else {
            const minutes = Math.floor(diff / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            timerElement.textContent = `Quiz Time Left: ${minutes}:${seconds.toString().padStart(2, "0")}`;
        }
    }

    updateTimer();
    setInterval(updateTimer, 1000);
}

function startPerQuestionTimer() {
    const timerElement = document.getElementById("question-timer");
    if (!timerElement) return;

    const startedAt = new Date(timerElement.dataset.startedAt);
    const durationSeconds = Number(timerElement.dataset.duration);
    const endTime = new Date(startedAt.getTime() + durationSeconds * 1000);

    function updateTimer() {
        const now = new Date();
        const diff = endTime.getTime() - now.getTime();

    if (diff <= 0) {

        timerElement.textContent = "Time's Up!";

        timerElement.style.color = "#ff4d4d";
        timerElement.style.fontWeight = "bold";

        const form = document.getElementById("question-form");

        if (form) {

            if (
                typeof progress !== "undefined" &&
                typeof totalQuestions !== "undefined" &&
                typeof window.moveQuizRocket === "function"
            ) {

                const nextPercent = Math.min(
                    progress + (100 / totalQuestions),
                    100
                );

                window.moveQuizRocket(nextPercent);

                setTimeout(() => {

                    HTMLFormElement.prototype.submit.call(form);

                }, 500);

            }
            else {

                HTMLFormElement.prototype.submit.call(form);

            }

        }

        clearInterval(interval);

        return;

    }

        const totalSeconds = Math.floor(diff / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        timerElement.textContent =
            `${minutes}:${seconds.toString().padStart(2, "0")}`;

        // Change appearance in the last 10 seconds
        if (totalSeconds <= 10) {
            timerElement.style.color = "red";
            timerElement.style.fontWeight = "bold";
        } else {
            // Restore normal appearance
            timerElement.style.color = "";
            timerElement.style.fontWeight = "";
        }
    }

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
}

document.addEventListener("DOMContentLoaded", () => {
    startQuizTimer();
    startPerQuestionTimer();
});
