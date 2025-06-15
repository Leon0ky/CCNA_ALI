from django.contrib import admin
# Import UserProfile here
from .models import Test, Question, Answer, TestAttempt, UserAnswer, UserProfile

# Register UserProfile so you can manage it in the Django admin
admin.site.register(UserProfile)
admin.site.register(Test)

# You can register others too if you want to see them in the default admin
# admin.site.register(Question)
# admin.site.register(Answer)
# admin.site.register(TestAttempt)
# admin.site.register(UserAnswer)