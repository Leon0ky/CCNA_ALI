import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import *

print('Recent test attempts:')
for attempt in TestAttempt.objects.all().order_by('-start_time')[:3]:
    print(f'  Attempt {attempt.id}: {attempt.user.username} - {attempt.test.name} ({attempt.test.test_type})')
    
print('\nRecent user answers:')
for ua in UserAnswer.objects.all().order_by('-id')[:5]:
    selected = [a.text for a in ua.selected_answers.all()]
    correct = [a.text for a in ua.question.answers.filter(is_correct=True)]
    print(f'  Q{ua.question.id}: Selected={selected}, Correct={correct}, MarkedCorrect={ua.is_correct}')

print('\nChecking a specific question for debugging:')
# Get the first question
if Question.objects.exists():
    q = Question.objects.first()
    print(f'Question: {q.text[:50]}...')
    for answer in q.answers.all():
        print(f'  Answer {answer.id}: "{answer.text}" - Correct: {answer.is_correct}')
