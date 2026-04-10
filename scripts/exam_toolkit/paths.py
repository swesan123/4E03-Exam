from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_DIR = REPO_ROOT / "sample questions"
DATA_DIR = REPO_ROOT / "data"
QUESTIONS_JSON = DATA_DIR / "questions.json"
QUESTION_TAGS_YAML = DATA_DIR / "question_tags.yaml"
USAGE_JSON = DATA_DIR / "usage.json"
BUILD_LATEX_DIR = REPO_ROOT / "build" / "latex"
GENERATED_EXAMS_DIR = REPO_ROOT / "generated_exams"
GENERATED_EXAMS_WORK_DIR = REPO_ROOT / "generated_exams_work"
