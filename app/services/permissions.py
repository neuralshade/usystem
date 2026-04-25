from app.models import MentorStudent


def get_student_assignment(student_id):
    return MentorStudent.query.filter_by(student_id=student_id).first()


def can_manage_student(current_user_id, current_role, student_id):
    if current_role not in ('mentor', 'teacher'):
        return False

    assignment = get_student_assignment(student_id)
    if not assignment:
        return current_role == 'teacher'

    return assignment.mentor_id == current_user_id


def can_access_student(current_user_id, current_role, student_id):
    if current_role not in ('mentor', 'teacher'):
        return False

    assignment = get_student_assignment(student_id)
    if not assignment:
        return True

    return assignment.mentor_id == current_user_id
