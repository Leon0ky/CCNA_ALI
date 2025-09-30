import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import Test

print('Current tests with positions:')
for test in Test.objects.all().order_by('position', 'name'):
    print(f'  {test.id}: {test.name} - Position: {test.position}')

print('\nUpdating positions to sequential order...')
for index, test in enumerate(Test.objects.all().order_by('name')):
    test.position = index
    test.save()
    print(f'  Updated {test.name} to position {index}')

print('\nFinal order:')
for test in Test.objects.all().order_by('position', 'name'):
    print(f'  {test.id}: {test.name} - Position: {test.position}')
