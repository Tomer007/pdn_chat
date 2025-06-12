import json

from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    with open("app/data/questions.json", "r", encoding="utf-8") as f:
        app.state.questions = json.load(f)


# Temporary dictionary to store user answers in memory
user_answers = {}


def get_question(question_number: int, questions: dict):
    """
    Fetch a specific question by its number.
    Returns the question text and its options.
    """
    
    # Check Part A questions (1-26)
    if 1 <= question_number <= 26:
        print("Part A")
        phase = "PartA"
    # Check Part B questions (27-37)
    elif 27 <= question_number <= 37:
        print("Part B")
        phase = "PartB"
    # Check Part C questions (38-42)
    elif 38 <= question_number <= 42:   
        print("Part C")
        phase = "PartC"
    # Check Part D questions (43-56)
    elif 43 <= question_number <= 56:
        phase = "PartD"
    # Check Part E questions (57-59)    
    elif 57 <= question_number <= 59:   
        phase = "PartE" 
    # Check Part F questions (60-65)
    elif 60 <= question_number <= 65:       
        phase = "PartF"
    else:
        return {"message": "No more questions."}

    # Get the question from the appropriate phase
    question = questions["phases"][phase]["questions"].get(str(question_number))

    if not question:
        return {"message": "No more questions."}

    return {
        "question_number": question_number,
        "question": question["text"],
        "options": question["options"],
        "stage": phase,
        "type": question.get("type"),
        "instructions": questions["phases"][phase].get("instructions", "")
    }


def submit_answer(question_number: int, selected_option_code: str, selected_option_text: str, ranking: dict = None,
                  email: str = None, questions: dict = None):
    """
    Submit an answer to a specific question.
    Stores the answer and returns the next question if available.
    """
    if not email:
        raise ValueError("Email is required")

    # Initialize user's answer dictionary if it doesn't exist
    if email not in user_answers:
        user_answers[email] = {}

    # Store the answer with all details
    # TODO check if we need the user_answer might be deleted
    user_answers[email][question_number] = {
        "code": selected_option_code,
        "text": selected_option_text,
        "ranking": ranking
    }

    next_question_number = question_number + 1
    next_question = questions.get(str(next_question_number))

    if not next_question:
        return {
            "message": "Questionnaire completed.",
            "answers": user_answers[email]
        }

    return {
        "question_number": next_question_number,
        "question": next_question["text"],
        "options": next_question["options"],
        "type": next_question.get("type"),
        "instructions": next_question.get("instructions")
    }
