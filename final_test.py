import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import *

print('=== Complete Test of the Learning Mode Fix ===')

# Find a learning mode test
learning_tests = Test.objects.filter(test_type='learning')
if learning_tests.exists():
    test = learning_tests.first()
    print(f'Testing with: {test.name}')
    
    # Get a question with answers
    if test.questions.exists():
        question = test.questions.first()
        print(f'Question: {question.text[:50]}...')
        
        # Show all answers
        for answer in question.answers.all():
            print(f'  Answer {answer.id}: "{answer.text}" - Correct: {answer.is_correct}')
        
        # Get the correct answer(s)
        correct_answers = question.answers.filter(is_correct=True)
        correct_ids = list(correct_answers.values_list('id', flat=True))
        print(f'\nCorrect answer IDs: {correct_ids}')
        
        # Simulate what happens in the form - user selects the correct answer
        selected_answer_ids_form = [str(id) for id in correct_ids]  # Form returns strings
        print(f'Form returns (strings): {selected_answer_ids_form}')
        
        # Apply our fix - convert to integers
        selected_answer_ids = [int(id) for id in selected_answer_ids_form]
        print(f'After conversion: {selected_answer_ids}')
        
        # Test the comparison logic from views.py
        correct_answer_ids = set(Answer.objects.filter(question=question, is_correct=True).values_list('id', flat=True))
        user_selected_ids = set(selected_answer_ids)
        
        is_correct = (correct_answer_ids == user_selected_ids)
        
        print(f'\nCorrect answer IDs (set): {correct_answer_ids}')
        print(f'User selected IDs (set): {user_selected_ids}')
        print(f'Is answer correct: {is_correct}')
        
        if is_correct:
            print('\n✅ SUCCESS: The fix works! Correct answers are now properly recognized.')
        else:
            print('\n❌ FAILED: The fix did not work.')
    else:
        print('No questions found in the test.')
else:
    print('No learning mode tests found.')
