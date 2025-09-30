import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import *

print('Testing the fix:')

# Simulate the fixed logic
if UserAnswer.objects.exists():
    ua = UserAnswer.objects.first()
    question = ua.question
    
    # Simulate form data (strings)
    form_selected_ids = [str(id) for id in ua.selected_answers.values_list('id', flat=True)]
    print(f'Form selected IDs (strings): {form_selected_ids}')
    
    # Apply the fix: convert to integers
    selected_answer_ids = [int(id) for id in form_selected_ids]
    print(f'After conversion to int: {selected_answer_ids}')
    
    # Get correct answers
    correct_answer_ids = set(Answer.objects.filter(question=question, is_correct=True).values_list('id', flat=True))
    user_selected_ids = set(selected_answer_ids)
    
    print(f'Correct answer IDs: {correct_answer_ids}')
    print(f'User selected IDs: {user_selected_ids}')
    
    # Test the comparison
    is_correct = (correct_answer_ids == user_selected_ids)
    print(f'Is correct (with fix): {is_correct}')
    
    # Show the original comparison that was failing
    user_selected_strings = set(form_selected_ids)
    is_correct_old = (correct_answer_ids == user_selected_strings)
    print(f'Is correct (old buggy way): {is_correct_old}')
