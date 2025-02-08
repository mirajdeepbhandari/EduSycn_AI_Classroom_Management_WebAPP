import random
import re
import json


def format_datetime(dt):
    # Directly format the datetime object
    formatted_date = dt.strftime('%Y-%m-%d, %I:%M %p')
    return formatted_date

def get_initials(name):
    parts = str(name).split()
    if len(parts) >= 2:
        initials = parts[0][0] + parts[1][0]
    elif len(parts) == 1:
        initials = parts[0][0]
    else:
        initials = ""
    return initials.upper()



def random_color(value):
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def get_filename(file_path):
    return file_path.split("\\")[-1]


def parse_questions(textout):
        questions = {}
        question_blocks = re.split(r'\*\*Question (\d+):\*\*', textout)[1:]
        
        for i in range(0, len(question_blocks), 2):
            q_number = int(question_blocks[i].strip())
            q_content = question_blocks[i + 1].strip().split("\n")
            
            question_text = q_content[0].strip()
            options = {}
            correct_answer = ""
            
            for line in q_content[1:]:
                match = re.match(r"([A-D])\) (.+)", line.strip())
                if match:
                    options[match[1]] = match[2]
                elif line.startswith("Correct Answer:"):
                    correct_answer = line.split(":")[1].strip()
            
            questions[q_number] = {
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer
            }
        
        return questions

def parse_json(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)  # Convert JSON string to dictionary
        except json.JSONDecodeError:
            return "Invalid JSON format"
    
    formatted_data = ""
    
    for key, item in data.items():
        question = item.get("question", "N/A")
        options = item.get("options", {})
        correct_answer = item.get("correct_answer", "N/A")
        
        formatted_data += f"{key}. {question}\n"
        for label, option in options.items():
            formatted_data += f"   {label}) {option}\n"
        
        formatted_data += f"   Correct Answer: {correct_answer}\n\n"
    
    return formatted_data

