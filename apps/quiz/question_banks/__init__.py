from . import science, grammar, mathematics
import importlib

QUESTION_BANK = {
    "science": science.QUESTIONS,
    "grammar": grammar.QUESTIONS,
    "mathematics": mathematics.QUESTIONS,
}
import importlib

def get_question_bank(topic: str):
    try:
        module = importlib.import_module(f"apps.quiz.question_banks.{topic}")
        return module.QUESTIONS
    except ModuleNotFoundError:
        return []