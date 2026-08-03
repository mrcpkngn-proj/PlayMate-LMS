document.addEventListener("DOMContentLoaded", () => {
  const mascotText = document.getElementById("mascot-text");
  const nextBtn = document.getElementById("next-instruction");
  const skipBtn = document.getElementById("skip-guide");

  const steps = [
    "Welcome, Teacher! Let’s start your quest to create a quiz…",
    "Step 1: Enter your quiz title and description.",
    "Step 2: Add your first question using the 'Add Question' button.",
    "Step 3: Fill in choices and mark the correct answer.",
    "Step 4: Set points and duration for each question.",
    "Step 5: Save your quiz and preview it before publishing!"
  ];

  let currentStep = 0;

  nextBtn.addEventListener("click", () => {
    currentStep++;
    if (currentStep < steps.length) {
      mascotText.textContent = steps[currentStep];
    } else {
      document.querySelector(".mascot-guide").style.display = "none";
    }
  });

  skipBtn.addEventListener("click", () => {
    document.querySelector(".mascot-guide").style.display = "none";
  });
});
