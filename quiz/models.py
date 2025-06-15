from django.db import models
from django.conf import settings
# Import Django's default User model
from django.contrib.auth.models import User
# Import signals for automatic profile creation
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg # For User.average_score if we add it back, though it's on CustomUser previously.
                                # Let's keep it here for now for safety.

# --- NEW: UserProfile Model ---
class UserProfile(models.Model):
    """
    Extends Django's default User model with additional fields.
    Linked via a OneToOneField.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    blocked_until = models.DateTimeField(null=True, blank=True) # Field for temporary blocking

    def __str__(self):
        return self.user.username + " Profile"

# --- NEW: Signals to Create/Save UserProfile Automatically ---
# This ensures every new User automatically gets a UserProfile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Creates a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Saves the UserProfile whenever the User is saved."""
    instance.userprofile.save()

# --- Your existing models below ---

# Define Test Types
TEST_TYPES = (
    ('learning', 'Learning Mode'),
    ('exam', 'Exam Mode'),
)

class Test(models.Model):
    """ Represents a type of test (e.g., 'Math Basics - Learning', 'Final Exam') """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    test_type = models.CharField(max_length=10, choices=TEST_TYPES, default='learning')

    def __str__(self):
        return f"{self.name} ({self.get_test_type_display()})"

class Question(models.Model):
    """ Represents a single multiple-choice question """
    test = models.ForeignKey(Test, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.text[:50] + '...' if len(self.text) > 50 else self.text

class Answer(models.Model):
    """ Represents an answer choice for a question """
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class TestAttempt(models.Model):
    """ Tracks a user's attempt at a specific test """
    # This foreign key correctly points to Django's default User model
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True) # Percentage or points
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.test.name} ({'Completed' if self.completed else 'In Progress'})"

class UserAnswer(models.Model):
    """ Stores the answers selected by a user for a specific question during an attempt """
    test_attempt = models.ForeignKey(TestAttempt, related_name='user_answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer) # User can select multiple answers
    is_correct = models.BooleanField(default=False) # Store if the user's selection for THIS question was correct

    def __str__(self):
        return f"Attempt {self.test_attempt.id} - Q: {self.question.id}"