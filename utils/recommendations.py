def generate_recommendations(student_data, predicted_score):
    """
    Generate actionable academic and behavioral recommendations 
    based on the student's metrics and their predicted final score.
    """
    suggestions = []

    # 1. Critical Score Intervention
    if predicted_score < 40.0:
        suggestions.append({
            "category": "Immediate Academic Support Required",
            "text": "Your predicted score is in the critical warning range (< 40%). We highly recommend scheduling an urgent meeting with your course advisor and enrolling in remedial tutoring classes immediately.",
            "priority": "HIGH"
        })
    elif predicted_score < 60.0:
        suggestions.append({
            "category": "Targeted Academic Support Recommended",
            "text": "Your predicted score is in the borderline/passing range (40%-60%). Seeking active peer study groups and school-provided extra coaching sessions will help stabilize your marks.",
            "priority": "MEDIUM"
        })

    # 2. Attendance Checks
    attendance = float(student_data.get('attendance', 100))
    if attendance < 75.0:
        suggestions.append({
            "category": "Attendance Improvement",
            "text": f"Your attendance is currently {attendance}%, which is below the standard minimum requirement of 75%. Try to attend all classes going forward, as regular attendance correlates strongly with higher scores.",
            "priority": "HIGH"
        })
    elif attendance < 85.0:
        suggestions.append({
            "category": "Attendance Stabilization",
            "text": f"Your attendance is {attendance}%. Try to minimize voluntary absences. Even missing a few lectures can cause gaps in cumulative subjects.",
            "priority": "MEDIUM"
        })

    # 3. Study Hours Checks
    study_hours = float(student_data.get('study_hours', 5))
    if study_hours < 4.0:
        suggestions.append({
            "category": "Daily Study Routine",
            "text": f"Your study duration is {study_hours} hours per day. We recommend increasing your self-study time to at least 4-5 hours per day, utilizing active recall and spaced repetition techniques.",
            "priority": "HIGH"
        })
    elif study_hours < 6.0:
        suggestions.append({
            "category": "Study Optimization",
            "text": f"You study {study_hours} hours per day. Consider dedicating an extra hour daily specifically for solving past examination papers and sample test sheets.",
            "priority": "LOW"
        })

    # 4. Assignments Completed Checks
    assignments = int(student_data.get('assignments', 10))
    if assignments < 6:
        suggestions.append({
            "category": "Assignment Submission",
            "text": f"You completed only {assignments}/10 assignments. Missing homework directly drops internal assessment marks and reduces understanding. Prioritize current submissions and seek extensions for late ones.",
            "priority": "HIGH"
        })
    elif assignments < 9:
        suggestions.append({
            "category": "Assignment Completeness",
            "text": f"You completed {assignments}/10 assignments. Aim for 100% completion to secure full internal grading allocations.",
            "priority": "MEDIUM"
        })

    # 5. Sleep Hours Checks
    sleep_hours = float(student_data.get('sleep_hours', 8))
    if sleep_hours < 6.0:
        suggestions.append({
            "category": "Sleep Schedule Correction",
            "text": f"You get {sleep_hours} hours of sleep. Sleeping less than 6 hours per day impairs cognitive function, concentration, and long-term memory. Aim for a consistent 7-8 hours, especially before exams.",
            "priority": "HIGH"
        })
    elif sleep_hours > 9.0:
        suggestions.append({
            "category": "Sleep Schedule Correction",
            "text": f"You get {sleep_hours} hours of sleep. Excess sleep can cause fatigue and lethargy. Aim to optimize your sleep to 7.5 to 8.5 hours to maximize productivity.",
            "priority": "LOW"
        })

    # 6. Class Participation & Engagement Checks
    participation = float(student_data.get('participation', 10))
    if participation < 5.0:
        suggestions.append({
            "category": "Classroom Engagement",
            "text": f"Your participation score is {participation}/10. Try to actively ask questions, answer prompts, and participate in classroom group tasks. It builds tutor rapport and boosts internal marks.",
            "priority": "MEDIUM"
        })

    # 7. Previous Marks & Core Revision
    prev_marks = float(student_data.get('prev_marks', 70))
    if prev_marks < 60.0:
        suggestions.append({
            "category": "Foundational Review",
            "text": f"With previous marks of {prev_marks}%, you might have gaps in core foundations. Dedicate the first 30 minutes of your study sessions to reviewing prior concepts before moving to new syllabus chapters.",
            "priority": "HIGH"
        })

    # 8. Discipline and Focus Checks
    discipline = float(student_data.get('discipline_score', 10))
    if discipline < 6.0:
        suggestions.append({
            "category": "Classroom Behavior & Discipline",
            "text": f"Your discipline score is {discipline}/10. Try to minimize distractions, avoid late submissions, and maintain respectful interactions in school. Discipline directly correlates with academic stability.",
            "priority": "MEDIUM"
        })

    # 9. Environmental Support Context
    internet = str(student_data.get('internet_access', 'Yes')).lower()
    if internet == 'no':
        suggestions.append({
            "category": "Resource Access",
            "text": "Since you lack home internet, utilize school computers, offline library books, or coordinate offline resources with peers to stay ahead in course study.",
            "priority": "LOW"
        })

    family_support = str(student_data.get('family_support', 'Yes')).lower()
    if family_support == 'no':
        suggestions.append({
            "category": "Support System",
            "text": "Academic success is easier with a support group. Consider forming peer study circles or talking to school counselors to establish a healthy emotional and academic backup.",
            "priority": "MEDIUM"
        })

    # 10. General Encouragement for top scorers
    if predicted_score >= 85.0 and len(suggestions) == 0:
        suggestions.append({
            "category": "Excellence Maintenance",
            "text": "Superb job! Your metrics point towards exceptional performance. Keep up your current routine, support your peers in group study, and challenge yourself with advanced project works.",
            "priority": "LOW"
        })
    elif predicted_score >= 80.0:
        suggestions.append({
            "category": "Maintenance Tip",
            "text": "You are on track for high performance. Maintain consistency in your study hours, sleep schedule, and attendance to lock in your predicted grade.",
            "priority": "LOW"
        })

    # Sort suggestions by priority: HIGH, then MEDIUM, then LOW
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return suggestions
