from django import forms
from django.utils import timezone # Needed for UserBlockForm's clean method
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm # <--- IMPORT UserCreationForm here
from django.contrib.auth.models import User # Required for UserCreationForm's Meta class
from .models import Question, Answer, Test, UserProfile # Import UserProfile


# --- Custom Admin Forms ---

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['test', 'text', 'image', 'explanation']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'textarea textarea-bordered w-full'}),
            'explanation': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            'test': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs'}),
            'image': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full max-w-xs'}),
        }
        labels = {
            'test': 'Assign to Test Type',
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }
        labels = {
            'text': 'Answer Text',
            'is_correct': 'Is Correct?',
        }


class TestForm(forms.ModelForm):
    """ Form for creating and editing Test objects """
    class Meta:
        model = Test
        fields = ['name', 'description', 'test_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'textarea textarea-bordered w-full'}),
            'test_type': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs'}),
        }
        labels = {
            'name': 'Test Name',
            'description': 'Description',
            'test_type': 'Test Behavior Type',
        }

# --- Quiz Taking Form ---

class UserAnswerForm(forms.Form):
    selected_answers = forms.ModelMultipleChoiceField(
        queryset=Answer.objects.none(), # Empty queryset initially
        widget=forms.CheckboxSelectMultiple(), # Allows multiple selections
        required=False, # User might not select anything (considered incorrect)
    )

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question') # Get the question object passed from the view
        super().__init__(*args, **kwargs)
        # Set the queryset for the selected_answers field based on the question
        self.fields['selected_answers'].queryset = question.answers.all()
        # Add DaisyUI classes to checkboxes
        self.fields['selected_answers'].widget.attrs.update({'class': 'checkbox checkbox-primary mr-2'})


# --- User Blocking Form ---

class UserBlockForm(forms.ModelForm):
    blocked_until = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input input-bordered w-full'}),
        label="Block Until (Leave blank to unblock)"
    )

    class Meta:
        model = UserProfile # Correctly targets UserProfile
        fields = ['blocked_until']

    def clean_blocked_until(self):
        blocked_until = self.cleaned_data.get('blocked_until')
        if blocked_until and blocked_until < timezone.now():
            raise forms.ValidationError("Block until date cannot be in the past.")
        return blocked_until

# --- Custom Authentication Form for Login Page ---
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI input classes to username and password fields
        self.fields['username'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your username' # Optional placeholder
        })
        self.fields['password'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your password' # Optional placeholder
        })

# --- NEW: Custom User Creation Form for Signup Page ---
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User # Use Django's default User model
        fields = UserCreationForm.Meta.fields # Inherit default fields (username, password, password2)
        # If you wanted to add email, it would be fields = UserCreationForm.Meta.fields + ('email',)
        # But we are using username as the primary field for UserCreationForm's built-in behavior.
        # If you wanted email to be the primary field, you would have to define a full CustomUser model with USERNAME_FIELD = 'email'
        # which we are not doing at this stage.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI input classes to all fields
        for field_name, field in self.fields.items():
            # For password fields, Django's UserCreationForm uses help_text as labels, so adjust placeholders
            placeholder_text = field.label or ''
            if field_name == 'password2':
                placeholder_text = 'Confirm Password'
            elif field_name == 'password1': # Using password1 directly might clash with help_text or label, usually default is fine
                placeholder_text = 'Password'
            elif field_name == 'username':
                placeholder_text = 'Choose a Username'

            field.widget.attrs.update({
                'class': 'input input-bordered w-full',
                'placeholder': placeholder_text
            })