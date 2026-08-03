// Namespace pattern for quiz form logic
const QuizForm = (() => {
    let questionsContainer, questionTemplate, choiceTemplate;

    // --- Core helpers ---
    function getQuestionIndex(questionBlock) {
        return Array.from(questionsContainer.querySelectorAll(".question-block"))
            .indexOf(questionBlock);
    }

    function setAnswerType(questionBlock, answerType) {
        const answerTypeInput = questionBlock.querySelector(".answer-type");
        const questionIndex = getQuestionIndex(questionBlock);
        answerTypeInput.value = answerType;

        const correctChoices = questionBlock.querySelectorAll(".correct-choice");
        let firstCheckedChoiceFound = false;

        correctChoices.forEach(input => {
            input.type = answerType === "single" ? "radio" : "checkbox";
            input.name = answerType === "single"
                ? "correct_choice_" + questionIndex
                : "correct_choice_" + questionIndex + "[]";

            if (answerType === "single" && input.checked) {
                if (firstCheckedChoiceFound) input.checked = false;
                firstCheckedChoiceFound = true;
            }
        });
    }

    function addChoice(choicesContainer, existingChoice = null) {
        const choiceContent = choiceTemplate.content.cloneNode(true);
        const choiceRow = choiceContent.querySelector(".choice-row");
        const choiceId = choiceRow.querySelector(".choice-id");
        const radio = choiceRow.querySelector(".correct-choice");
        const textInput = choiceRow.querySelector(".choice-text");

        if (existingChoice) {
            choiceId.value = existingChoice.id;
            textInput.value = existingChoice.text;
            radio.checked = existingChoice.is_correct;
        }

        choiceRow.querySelector(".remove-choice").addEventListener("click", () => {
            choiceRow.remove();
            refreshQuestionFields();
        });

        choicesContainer.appendChild(choiceContent);
        refreshQuestionFields();
    }

    function addQuestion(existingQuestion = null) {
        if (!questionTemplate || !choiceTemplate) {
            console.error("Templates not found in DOM!");
            return;
        }
        const questionContent = questionTemplate.content.cloneNode(true);
        const questionBlock = questionContent.querySelector(".question-block");

        const questionId = questionBlock.querySelector(".question-id");
        const questionText = questionBlock.querySelector(".question-text");
        const questionPoints = questionBlock.querySelector(".question-points");
        const answerTypeInput = questionBlock.querySelector(".answer-type");

        if (existingQuestion) {
            questionId.value = existingQuestion.id;
            questionText.value = existingQuestion.text;
            questionPoints.value = existingQuestion.points;
            answerTypeInput.value = existingQuestion.answer_type || "single";
        }

        const choicesContainer = questionBlock.querySelector(".choices-container");

        questionBlock.querySelector(".add-choice").addEventListener("click", () => addChoice(choicesContainer));
        questionBlock.querySelector(".set-single-answer").addEventListener("click", () => setAnswerType(questionBlock, "single"));
        questionBlock.querySelector(".set-multiple-answers").addEventListener("click", () => setAnswerType(questionBlock, "multiple"));
        questionBlock.querySelector(".remove-question").addEventListener("click", () => {
            questionBlock.remove();
            refreshQuestionFields();
        });

        const timerElement = questionBlock.querySelector(".question-timer");
        if (timerElement) {
            startQuestionTimer(timerElement, existingQuestion ? existingQuestion.duration : 30);
        }

        questionsContainer.appendChild(questionContent);

        if (existingQuestion) {
            existingQuestion.choices.forEach(choice => addChoice(choicesContainer, choice));
        } else {
            addChoice(choicesContainer);
            addChoice(choicesContainer);
        }

        refreshQuestionFields();
    }

    function refreshQuestionFields() {
        const questionBlocks = questionsContainer.querySelectorAll(".question-block");

        questionBlocks.forEach((questionBlock, questionIndex) => {
            questionBlock.querySelector(".question-number").textContent = questionIndex + 1;
            const answerType = questionBlock.querySelector(".answer-type").value;
            const choiceRows = questionBlock.querySelectorAll(".choice-row");

            choiceRows.forEach((choiceRow, choiceIndex) => {
                const choiceId = choiceRow.querySelector(".choice-id");
                const correctChoice = choiceRow.querySelector(".correct-choice");
                const choiceText = choiceRow.querySelector(".choice-text");

                choiceId.name = "choice_id_" + questionIndex + "[]";
                choiceText.name = "choice_text_" + questionIndex + "[]";

                if (answerType === "single") {
                    correctChoice.type = "radio";
                    correctChoice.name = "correct_choice_" + questionIndex;
                } else {
                    correctChoice.type = "checkbox";
                    correctChoice.name = "correct_choice_" + questionIndex;
                }

                correctChoice.value = choiceIndex.toString();
            });
        });
    }

    // --- Suggestions submodule ---
    const Suggestions = (() => {
        function init() {
            document.getElementById("suggest-questions").addEventListener("click", fetchSuggestions);
            document.getElementById("confirm-suggestions").addEventListener("click", confirmSuggestions);
            document.getElementById("reject-suggestions").addEventListener("click", rejectSuggestions);
        }

        function fetchSuggestions() {
            const topics = document.getElementById("topics").value;

            fetch("/quiz/suggest_questions/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ topics: topics })
            })
            .then(response => response.json())
            .then(data => {
                const previewBox = document.getElementById("suggestions-preview");
                const previewList = document.getElementById("preview-list");
                previewList.innerHTML = "";

                if (data.suggestions.length > 0) {
                    previewBox.style.display = "block";
                    data.suggestions.forEach((q, idx) => {
                        const item = document.createElement("p");
                        item.textContent = (idx+1) + ". " + q.text + " (" + q.choices.join(", ") + ")";
                        previewList.appendChild(item);
                    });
                    previewList.dataset.suggestions = JSON.stringify(data.suggestions);
                } else {
                    previewBox.style.display = "none";
                    alert("No suggestions found for that topic.");
                }
            })
            .catch(err => console.error("Error fetching suggestions:", err));
        }

        function confirmSuggestions() {
            const previewList = document.getElementById("preview-list");
            const suggestions = JSON.parse(previewList.dataset.suggestions || "[]");

            if (questionsContainer.querySelectorAll(".question-block").length === 1) {
                const firstBlock = questionsContainer.querySelector(".question-block");
                const textArea = firstBlock.querySelector(".question-text");
                if (!textArea.value.trim()) {
                    firstBlock.remove();
                }
            }

            suggestions.forEach(q => {
                addQuestion({
                    id: "",
                    text: q.text,
                    points: 1,
                    answer_type: "single",
                    choices: q.choices.map((c, idx) => ({
                        id: "",
                        text: c,
                        is_correct: q.correct.includes(idx)
                    }))
                });
            });

            document.getElementById("suggestions-preview").style.display = "none";
            document.getElementById("preview-list").innerHTML = "";
        }

        function rejectSuggestions() {
            document.getElementById("suggestions-preview").style.display = "none";
            document.getElementById("preview-list").innerHTML = "";
        }

        return { init };
    })();

    // Expose public API
    return {
        addQuestion,
        addChoice,
        setAnswerType,
        refreshQuestionFields,
        Suggestions,
        initDOM: () => {
            questionsContainer = document.getElementById("questions-container");
            questionTemplate = document.getElementById("question-template");
            choiceTemplate = document.getElementById("choice-template");
        }
    };
})();

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    QuizForm.initDOM();

    const quizDataElement = document.getElementById("quiz-data");
    const quizData = quizDataElement ? JSON.parse(quizDataElement.textContent) : [];

    if (quizData.length > 0) {
        quizData.forEach(q => QuizForm.addQuestion(q));
    } else {
        QuizForm.addQuestion();
    }

    const addBtn = document.getElementById("add-question");
    if (addBtn) {
        addBtn.addEventListener("click", () => QuizForm.addQuestion());
    }

    QuizForm.Suggestions.init();
});

document.addEventListener("DOMContentLoaded", function () {

    // radio buttons generated by ModelForm
    const displayModes = document.querySelectorAll(
        'input[name="display_mode"]'
    );

    // checkbox generated by ModelForm
    const timerCheckbox = document.querySelector(
        'input[name="use_question_timer"]'
    );

    if (!timerCheckbox) return;

    // Usually Django renders the checkbox inside a <p>
    const timerRow = timerCheckbox.closest("p");

    function updateVisibility() {

        const selected = document.querySelector(
            'input[name="display_mode"]:checked'
        );

        if (!selected) return;

        if (selected.value === "per_question") {
            timerRow.style.display = "";
        } else {
            timerRow.style.display = "none";

            // automatically disable it
            timerCheckbox.checked = false;
        }
    }

    displayModes.forEach(radio => {
        radio.addEventListener("change", updateVisibility);
    });

    updateVisibility();
});