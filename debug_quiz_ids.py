import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import *

# Debug the ID type issue
print('Debugging ID types in answer checking:')

# Get a recent user answer
if UserAnswer.objects.exists():
    ua = UserAnswer.objects.first()
    print(f'Question: {ua.question.text[:50]}...')
    
    # Get the correct answer IDs as they're stored in the database
    correct_answer_ids = Answer.objects.filter(question=ua.question, is_correct=True).values_list('id', flat=True)
    print(f'Correct answer IDs from DB (type): {list(correct_answer_ids)} ({type(list(correct_answer_ids)[0])})')
    
    # Get the user's selected answer IDs
    user_selected_ids = ua.selected_answers.values_list('id', flat=True)
    print(f'User selected IDs from DB (type): {list(user_selected_ids)} ({type(list(user_selected_ids)[0])})')
    
    # Simulate what happens in the form processing
    print('\nSimulating form data processing:')
    # Form typically returns string IDs
    form_selected_ids = [str(id) for id in user_selected_ids]
    print(f'Form selected IDs (strings): {form_selected_ids} ({type(form_selected_ids[0])})')
    
    # Check what happens when we convert to int
    form_selected_ids_int = [int(id) for id in form_selected_ids]
    print(f'Form selected IDs (converted to int): {form_selected_ids_int} ({type(form_selected_ids_int[0])})')
    
    # Test the comparison
    correct_set = set(correct_answer_ids)
    user_set = set(form_selected_ids)  # This is what's happening in the bug - comparing int with str
    user_set_int = set(form_selected_ids_int)  # This is what should happen
    
    print(f'\nComparison test:')
    print(f'Correct IDs set: {correct_set}')
    print(f'User IDs set (strings): {user_set}')
    print(f'User IDs set (ints): {user_set_int}')
    print(f'Correct == User (strings): {correct_set == user_set}')
    print(f'Correct == User (ints): {correct_set == user_set_int}')
