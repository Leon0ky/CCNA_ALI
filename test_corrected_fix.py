import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import *
from quiz.forms import UserAnswerForm

print('=== Testing the corrected fix ===')

# Get a question to test with
if Question.objects.exists():
    question = Question.objects.first()
    print(f'Testing with question: {question.text[:50]}...')
    
    # Simulate form data - the form returns Answer objects, not IDs
    correct_answers = question.answers.filter(is_correct=True)
    print(f'Correct answers: {[a.text for a in correct_answers]}')
    
    # Simulate what the form returns
    selected_answer_objects = list(correct_answers)  # Form returns Answer objects
    print(f'Form returns Answer objects: {selected_answer_objects}')
    
    # Apply the corrected fix
    selected_answer_ids = [answer.id for answer in selected_answer_objects]
    print(f'Extracted IDs: {selected_answer_ids}')
    
    # Test the comparison logic
    correct_answer_ids = set(Answer.objects.filter(question=question, is_correct=True).values_list('id', flat=True))
    user_selected_ids = set(selected_answer_ids)
    
    is_correct = (correct_answer_ids == user_selected_ids)
    
    print(f'Correct answer IDs: {correct_answer_ids}')
    print(f'User selected IDs: {user_selected_ids}')
    print(f'Is correct: {is_correct}')
    
    if is_correct:
        print('✅ SUCCESS: The corrected fix works!')
    else:
        print('❌ FAILED: Something is still wrong.')
else:
    print('No questions found.')
