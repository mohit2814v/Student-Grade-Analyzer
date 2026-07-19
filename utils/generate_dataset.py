import os
import random
import numpy as np
import pandas as pd

def generate_student_dataset(output_path, num_samples=1000, seed=42):
    """
    Generates a realistic student performance dataset with correlated features.
    Saves it as a CSV file to output_path.
    """
    np.random.seed(seed)
    random.seed(seed)

    first_names = [
        "Emma", "Liam", "Olivia", "Noah", "Ava", "Oliver", "Sophia", "Elijah", "Isabella", "James",
        "Charlotte", "Benjamin", "Amelia", "Lucas", "Mia", "Alexander", "Harper", "Mason", "Evelyn", "Michael",
        "Abigail", "Ethan", "Emily", "Daniel", "Elizabeth", "Jacob", "Sofia", "Logan", "Avery", "Jackson",
        "Ella", "Levi", "Madison", "Sebastian", "Scarlett", "Mateo", "Victoria", "Jack", "Aria", "Owen",
        "Grace", "Theodore", "Chloe", "Aiden", "Camila", "Samuel", "Penelope", "Joseph", "Riley", "John"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
        "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
    ]

    data = []

    for i in range(num_samples):
        # Student Name
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Demographic Info
        age = int(np.random.choice([16, 17, 18, 19, 20, 21]))
        gender = random.choice(["Male", "Female"])
        
        # Environmental Support
        internet_access = np.random.choice(["Yes", "No"], p=[0.85, 0.15])
        family_support = np.random.choice(["Yes", "No"], p=[0.75, 0.25])
        parental_education = np.random.choice(["Low", "Medium", "High"], p=[0.20, 0.50, 0.30])
        tuition = np.random.choice(["Yes", "No"], p=[0.35, 0.65])
        extracurricular = np.random.choice(["Yes", "No"], p=[0.45, 0.55])
        
        # Study habits & Behaviors
        study_hours = round(float(np.random.uniform(1.0, 10.0)), 1)
        attendance = round(float(np.random.beta(3, 1.5) * 60 + 40), 1)  # Skewed towards 75, goes down to 40
        sleep_hours = round(float(np.random.normal(7.0, 1.2)), 1)
        sleep_hours = max(4.0, min(10.0, sleep_hours))
        
        discipline_score = round(float(np.random.normal(7.0, 1.8)), 1)
        discipline_score = max(1.0, min(10.0, discipline_score))
        
        participation = round(float(np.random.normal(6.0, 2.2)), 1)
        participation = max(1.0, min(10.0, participation))

        assignments = int(np.random.choice(range(11), p=[0.05, 0.05, 0.05, 0.05, 0.05, 0.10, 0.12, 0.15, 0.13, 0.13, 0.12]))
        
        # Previous Academic Marks (0 - 100)
        prev_marks = round(float(np.random.normal(62, 16)), 1)
        prev_marks = max(30.0, min(100.0, prev_marks))

        # Academic assessments (correlated with prev_marks and study_hours)
        internal_marks = round(float(prev_marks * 0.2 + study_hours * 1.2 + np.random.normal(5, 2)), 1)
        internal_marks = max(0.0, min(30.0, internal_marks))
        
        practical_marks = round(float(attendance * 0.15 + participation * 0.8 + np.random.normal(6, 3)), 1)
        practical_marks = max(0.0, min(30.0, practical_marks))
        
        quiz_marks = round(float(prev_marks * 0.1 + study_hours * 0.5 + np.random.normal(4, 1.5)), 1)
        quiz_marks = max(0.0, min(20.0, quiz_marks))
        
        project_marks = round(float(prev_marks * 0.3 + participation * 1.0 + np.random.normal(12, 4)), 1)
        project_marks = max(0.0, min(50.0, project_marks))

        # Calculate Final Score using a linear equation + corrections + noise
        # This matches the physical constraints of grading
        score_base = (
            0.22 * prev_marks +                      # max 22
            0.22 * attendance +                      # max 22
            0.15 * (internal_marks * 100.0 / 30.0) +  # max 15
            0.10 * (practical_marks * 100.0 / 30.0) + # max 10
            0.05 * (quiz_marks * 100.0 / 20.0) +      # max 5
            0.08 * (project_marks * 100.0 / 50.0) +   # max 8
            1.0 * study_hours +                      # max 10
            0.4 * assignments +                      # max 4
            0.2 * participation +                    # max 2
            0.2 * discipline_score                   # max 2
        )  # Absolute Max = 100

        # Adjustments based on Sleep
        sleep_effect = 0.0
        if 7.0 <= sleep_hours <= 8.5:
            sleep_effect = 2.0
        elif sleep_hours < 5.5:
            sleep_effect = -4.0
        elif sleep_hours > 9.0:
            sleep_effect = -1.5

        # Adjustments based on Environment & Demographics
        env_effect = 0.0
        if internet_access == "Yes": env_effect += 1.5
        if family_support == "Yes": env_effect += 1.0
        if tuition == "Yes": env_effect += 1.0
        if extracurricular == "Yes": env_effect += 0.5
        
        if parental_education == "High": env_effect += 1.5
        elif parental_education == "Low": env_effect -= 1.5
        
        if gender == "Female": env_effect += 0.5  # slight demographic variable

        noise = np.random.normal(0, 2.0)
        
        final_score = score_base + sleep_effect + env_effect + noise
        final_score = round(max(0.0, min(100.0, final_score)), 1)

        data.append({
            "name": name,
            "age": age,
            "gender": gender,
            "study_hours": study_hours,
            "attendance": attendance,
            "prev_marks": prev_marks,
            "assignments": assignments,
            "participation": participation,
            "sleep_hours": sleep_hours,
            "internet_access": internet_access,
            "family_support": family_support,
            "parental_education": parental_education,
            "tuition": tuition,
            "extracurricular": extracurricular,
            "discipline_score": discipline_score,
            "internal_marks": internal_marks,
            "practical_marks": practical_marks,
            "quiz_marks": quiz_marks,
            "project_marks": project_marks,
            "final_score": final_score
        })

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated dataset with {num_samples} samples at: {output_path}")

if __name__ == "__main__":
    import sys
    path = "dataset/student_data.csv"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    generate_student_dataset(path)
