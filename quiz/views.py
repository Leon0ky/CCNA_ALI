from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.db.models import Count # For counting questions (already imported)
from django.http import JsonResponse
import json

# Import Django's default User model
from django.contrib.auth.models import User
# Import your custom UserProfile model and the forms
from .models import Test, Question, Answer, TestAttempt, UserAnswer, UserProfile
from .forms import QuestionForm, AnswerForm, UserAnswerForm, TestForm, UserBlockForm, CustomUserCreationForm


# --- Authentication Views ---


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # <--- USE CustomUserCreationForm
        if form.is_valid():
            user = form.save()
            # Log the user in after successful signup
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('test_list')  # Redirect to tests page or landing
    else:
        form = CustomUserCreationForm() # <--- USE CustomUserCreationForm
    return render(request, 'registration/signup.html', {'form': form})

# Django's built-in login/logout views via accounts/ urls are used automatically.
# Their templates are expected in registration/login.html and registration/logged_out.html


# --- General Views ---

def landing_page(request):
    # Simple landing page view
    return render(request, 'quiz/landing_page.html')

@login_required
def test_list(request):
    # --- MODIFIED: Annotate tests with question_count and order by position ---
    tests = Test.objects.annotate(question_count=Count('questions')).order_by('position', 'name')
    # --- END MODIFIED ---
    return render(request, 'quiz/test_list.html', {'tests': tests})


# --- Quiz Taking Views ---

@login_required
def start_test(request, test_id):
    # Check if user is blocked via their UserProfile
    if request.user.userprofile.blocked_until and request.user.userprofile.blocked_until > timezone.now():
        messages.error(request, "You are temporarily blocked from taking tests until " + request.user.userprofile.blocked_until.strftime("%Y-%m-%d %H:%M"))
        return redirect('test_list') # Redirect back to test list or home

    test = get_object_or_404(Test, id=test_id)

    # Create a new test attempt
    attempt = TestAttempt.objects.create(user=request.user, test=test)

    # Get all questions for this test
    questions = list(test.questions.all())

    # Redirect to the first question (index 0)
    return redirect(reverse('take_question', args=[attempt.id, 0]))

@login_required
def take_question(request, attempt_id, question_index):
    # Check if user is blocked via their UserProfile
    if request.user.userprofile.blocked_until and request.user.userprofile.blocked_until > timezone.now():
        messages.error(request, "You are temporarily blocked from taking tests until " + request.user.userprofile.blocked_until.strftime("%Y-%m-%d %H:%M"))
        return redirect('test_list') # Redirect back to test list or home

    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user, completed=False)
    test = attempt.test
    questions = list(test.questions.all())
    total_questions = len(questions)

    if question_index >= total_questions:
        # All questions answered, finish the test
        return redirect(reverse('finish_test', args=[attempt.id]))

    current_question = questions[question_index]
    answers = current_question.answers.all()

    # Check if user has already answered this question in this attempt
    existing_user_answer = UserAnswer.objects.filter(
        test_attempt=attempt,
        question=current_question
    ).first()

    if request.method == 'POST':
        # Use the form to handle selected answers
        form = UserAnswerForm(request.POST, question=current_question)
        if form.is_valid():
            selected_answer_objects = form.cleaned_data['selected_answers']
            # Extract IDs from Answer objects for comparison
            selected_answer_ids = [answer.id for answer in selected_answer_objects]

            # Use a transaction for atomic save
            with transaction.atomic():
                # If already answered, update or delete old and create new
                if existing_user_answer:
                    existing_user_answer.selected_answers.clear() # Clear previous selection
                    existing_user_answer.delete() # Or update

                # Create UserAnswer
                user_answer = UserAnswer.objects.create(
                    test_attempt=attempt,
                    question=current_question,
                    is_correct=False # Will determine correctness on finish for exam mode
                )
                user_answer.selected_answers.set(selected_answer_objects) # Add selected answers

                # In Learning Mode, determine correctness and show feedback immediately
                if test.test_type == 'learning':
                    # Check if the user's selected answers exactly match the correct answers
                    correct_answer_ids = set(Answer.objects.filter(question=current_question, is_correct=True).values_list('id', flat=True))
                    user_selected_ids = set(selected_answer_ids)

                    is_correct = (correct_answer_ids == user_selected_ids)
                    user_answer.is_correct = is_correct
                    user_answer.save()

                    # For simplicity, let's render feedback on the same page
                    context = {
                        'attempt': attempt,
                        'question': current_question,
                        'answers': answers,
                        'form': form,
                        'question_index': question_index,
                        'total_questions': total_questions,
                        'is_learning_mode': test.test_type == 'learning',
                        'user_submitted': True, # Flag to show feedback
                        'user_answer_object': user_answer,
                        'is_user_correct': is_correct,
                        'correct_answers': Answer.objects.filter(question=current_question, is_correct=True),
                    }
                    # We will add a "Next" button in the template
                    return render(request, 'quiz/take_question.html', context)

                # In Exam Mode, just save the answer and move to the next question
                elif test.test_type == 'exam':
                    # Correctness is determined on finish_test
                    next_question_index = question_index + 1
                    return redirect(reverse('take_question', args=[attempt.id, next_question_index]))

        # If form is invalid, re-render the page with errors
        else:
             context = {
                'attempt': attempt,
                'question': current_question,
                'answers': answers,
                'form': form,
                'question_index': question_index,
                'total_questions': total_questions,
                'is_learning_mode': test.test_type == 'learning',
                'user_submitted': False, # No feedback yet
             }
             return render(request, 'quiz/take_question.html', context)

    else: # GET request
        # Create the form for selecting answers
        form = UserAnswerForm(question=current_question) # Pass the question to the form

        context = {
            'attempt': attempt,
            'question': current_question,
            'answers': answers,
            'form': form,
            'question_index': question_index,
            'total_questions': total_questions,
            'is_learning_mode': test.test_type == 'learning',
            'user_submitted': False, # No feedback yet
        }
        return render(request, 'quiz/take_question.html', context)


@login_required
def finish_test(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user, completed=False)
    test = attempt.test
    questions = list(test.questions.all())
    total_questions = len(questions)
    correct_count = 0

    # Calculate score if in Exam Mode
    if test.test_type == 'exam':
        for question in questions:
            try:
                user_answer = UserAnswer.objects.get(test_attempt=attempt, question=question)
                # Get correct answers for this question
                correct_answers = set(Answer.objects.filter(question=question, is_correct=True).values_list('id', flat=True))
                # Get user's selected answers
                user_selected_answers = set(user_answer.selected_answers.values_list('id', flat=True))

                # User is correct only if their selected answers exactly match the correct ones
                is_correct = (correct_answers == user_selected_answers)

                # Update the is_correct field on the UserAnswer model for exam mode results display
                user_answer.is_correct = is_correct
                user_answer.save()

                if is_correct:
                    correct_count += 1

            except UserAnswer.DoesNotExist:
                # User didn't answer this question, it's incorrect
                pass # correct_count remains the same

        # Calculate score (percentage)
        if total_questions > 0:
            score = (correct_count / total_questions) * 100
        else:
            score = 0.0

        attempt.score = round(score, 2) # Store score with 2 decimal places

    # Mark attempt as completed
    attempt.end_time = timezone.now()
    attempt.completed = True
    attempt.save()

    # Redirect to results page
    return redirect(reverse('test_results', args=[attempt.id]))


@login_required
def test_results(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user, completed=True)
    test = attempt.test
    user_answers = attempt.user_answers.all().select_related('question').prefetch_related('selected_answers', 'question__answers')

    # Collect results data
    results_data = []
    for ua in user_answers:
        question = ua.question
        correct_answers = Answer.objects.filter(question=question, is_correct=True)
        selected_answers = ua.selected_answers.all()

        # Determine if the user's selection was exactly correct (needed for exam mode display)
        correct_ids = set(correct_answers.values_list('id', flat=True))
        selected_ids = set(selected_answers.values_list('id', flat=True))
        is_correct_for_display = (correct_ids == selected_ids)


        results_data.append({
            'question': question,
            'user_selected_answers': selected_answers,
            'correct_answers': correct_answers,
            'is_user_correct': is_correct_for_display, # Use this for exam mode
        })

    context = {
        'attempt': attempt,
        'test': test,
        'results_data': results_data,
        'is_learning_mode': test.test_type == 'learning',
    }
    return render(request, 'quiz/test_results.html', context)


# --- Custom Admin Views ---

# Helper to check if user is staff (can be improved with custom group checks)
def is_staff_check(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_check)
def reorder_tests(request):
    """Handle test reordering via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            test_ids = data.get('test_ids', [])
            
            # Update positions for each test
            for index, test_id in enumerate(test_ids):
                Test.objects.filter(id=test_id).update(position=index)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# --- MODIFIED: custom_admin_questions to handle optional test_id ---
@user_passes_test(is_staff_check)
def custom_admin_questions(request, test_id=None): # <--- Added optional test_id parameter
    questions_queryset = Question.objects.all().select_related('test').prefetch_related('answers')
    test_obj = None # Initialize test_obj to None

    if test_id:
        test_obj = get_object_or_404(Test, id=test_id)
        questions_queryset = questions_queryset.filter(test=test_obj) # Filter by the specific test

    context = {
        'questions': questions_queryset,
        'test_obj': test_obj, # Pass the Test object to the template
    }
    return render(request, 'quiz/custom_admin/questions_list.html', context)

# Use inline formset to manage answers along with the question
AnswerInlineFormSet = inlineformset_factory(Question, Answer, form=AnswerForm, extra=4, can_delete=True)

# --- MODIFIED: custom_admin_add_question to handle optional test_id ---
@user_passes_test(is_staff_check)
def custom_admin_add_question(request, test_id=None): # <--- Added optional test_id parameter
    test_obj = None # Initialize test_obj to None
    initial_data = {} # Dictionary for initial form data

    if test_id:
        test_obj = get_object_or_404(Test, id=test_id)
        initial_data['test'] = test_obj # Pre-fill the test field

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES) # Initial data is not passed directly here if POST
        formset = AnswerInlineFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            # Ensure the test field is correctly set, especially if it was pre-filled or hidden
            if test_obj: # If coming from a test-specific URL
                question.test = test_obj
            
            # Ensure at least one correct answer is selected (basic validation)
            answers_data = formset.cleaned_data
            has_correct_answer = any(answer.get('is_correct') for answer in answers_data if not answer.get('DELETE'))

            if has_correct_answer:
                # Ensure exactly 4 answers are submitted
                valid_answers_count = sum(1 for form in formset if not form.cleaned_data.get('DELETE'))
                if valid_answers_count == 4:
                    question.save() # Save question first to get an ID
                    formset.instance = question # Set the instance for the formset
                    formset.save()
                    # Redirect back to test-specific questions list if applicable, else general questions
                    if test_obj:
                        messages.success(request, "Question added successfully to " + test_obj.name + ".")
                        return redirect(reverse('custom_admin_test_questions', args=[test_obj.id]))
                    else:
                        messages.success(request, "Question added successfully.")
                        # Check for next parameter to redirect back to the correct page
                        next_url = request.POST.get('next') or request.GET.get('next')
                        if next_url:
                            return redirect(next_url)
                        return redirect('custom_admin_questions')
                else:
                    form.add_error(None, "Please provide exactly 4 answers.") # Add error to main form
            else:
                form.add_error(None, "Please mark at least one answer as correct.") # Add error to main form
        else:
            # If form or formset is invalid, add errors to context
            if not form.is_valid():
                messages.error(request, "Please correct the errors in the question form.")
            if not formset.is_valid():
                messages.error(request, "Please correct the errors in the answers.")

    else: # GET request
        form = QuestionForm(initial=initial_data) # <--- Pass initial data here
        formset = AnswerInlineFormSet() # Empty formset for adding new

    context = {
        'form': form,
        'formset': formset,
        'is_edit': False,
        'test_obj': test_obj, # Pass the Test object to the template
    }
    return render(request, 'quiz/custom_admin/question_form.html', context)


@user_passes_test(is_staff_check)
def custom_admin_edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    AnswerInlineFormSet = inlineformset_factory(Question, Answer, form=AnswerForm, extra=0, can_delete=True) # Extra=0 for editing

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES, instance=question)
        formset = AnswerInlineFormSet(request.POST, request.FILES, instance=question)
        if form.is_valid() and formset.is_valid():
            # Ensure at least one correct answer is selected (basic validation)
            answers_data = formset.cleaned_data
            has_correct_answer = any(answer.get('is_correct') for answer in answers_data if not answer.get('DELETE'))

            if has_correct_answer:
                # Ensure exactly 4 answers remain after potential deletion
                valid_answers_count = sum(1 for form in formset if not form.cleaned_data.get('DELETE'))
                if valid_answers_count == 4:
                    form.save()
                    formset.save()
                    messages.success(request, "Question updated successfully.")
                    # Check for next parameter to redirect back to the correct page
                    next_url = request.POST.get('next') or request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('custom_admin_questions') # Fallback to general questions list
                else:
                    form.add_error(None, "Please ensure exactly 4 answers remain.") # Add error to main form
            else:
                form.add_error(None, "Please mark at least one answer as correct.") # Add error to main form
        else:
            # If form or formset is invalid, add errors to context
            if not form.is_valid():
                messages.error(request, "Please correct the errors in the question form.")
            if not formset.is_valid():
                messages.error(request, "Please correct the errors in the answers.")


    else: # GET request
        form = QuestionForm(instance=question)
        formset = AnswerInlineFormSet(instance=question) # Populate formset with existing answers

    context = {
        'form': form,
        'formset': formset,
        'question': question,
        'is_edit': True,
    }
    return render(request, 'quiz/custom_admin/question_form.html', context)


@user_passes_test(is_staff_check)
def custom_admin_delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    next_url = request.GET.get('next') or request.POST.get('next')
    redirect_url = next_url if next_url else reverse('custom_admin_questions')
    if request.method == 'POST':
        question.delete()
        messages.success(request, f"Question '{question.text[:30]}...' deleted successfully.")
        return redirect(redirect_url)
    # Confirmation page, pass redirect_url for cancel button
    return render(request, 'quiz/custom_admin/question_confirm_delete.html', {
        'question': question,
        'redirect_url': redirect_url
    })

@user_passes_test(is_staff_check)
def custom_admin_users(request):
    filter_status = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')

    users_queryset = User.objects.select_related('userprofile').order_by('username')

    if search_query:
        users_queryset = users_queryset.filter(username__icontains=search_query) | \
                         users_queryset.filter(email__icontains=search_query)

    if filter_status == 'staff':
        users_queryset = users_queryset.filter(is_staff=True)
    elif filter_status == 'normal':
        users_queryset = users_queryset.filter(is_staff=False)
    elif filter_status == 'blocked':
        users_queryset = users_queryset.filter(userprofile__blocked_until__isnull=False, userprofile__blocked_until__gt=timezone.now())
    elif filter_status == 'active':
        users_queryset = users_queryset.filter(userprofile__blocked_until__isnull=True) | \
                         users_queryset.filter(userprofile__blocked_until__lt=timezone.now()) # not blocked or block expired

    context = {
        'users': users_queryset,
        'filter_status': filter_status,
        'search_query': search_query,
        'now': timezone.now(), # Pass current time for template logic
    }
    return render(request, 'quiz/custom_admin/users_list.html', context)


# --- Custom Admin Views (Tests) ---

@user_passes_test(is_staff_check)
def custom_admin_tests(request):
    """ List all Test types """
    # --- MODIFIED: Annotate tests with question_count ---
    tests = Test.objects.annotate(question_count=Count('questions')).order_by('name')
    # --- END MODIFIED ---
    context = {
        'tests': tests,
    }
    return render(request, 'quiz/custom_admin/admin_tests_list.html', context)

@user_passes_test(is_staff_check)
def custom_admin_add_test(request):
    """ Add a new Test type """
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Test added successfully.")
            return redirect('custom_admin_tests') # Redirect back to the list
    else: # GET request
        form = TestForm()

    context = {
        'form': form,
        'is_edit': False, # Flag to indicate whether we're adding or editing
    }
    return render(request, 'quiz/custom_admin/test_form.html', context)


@user_passes_test(is_staff_check)
def custom_admin_edit_test(request, test_id):
    """ Edit an existing Test type """
    test = get_object_or_404(Test, id=test_id)

    if request.method == 'POST':
        form = TestForm(request.POST, instance=test) # Pass instance for editing
        if form.is_valid():
            form.save()
            messages.success(request, "Test updated successfully.")
            return redirect('custom_admin_tests') # Redirect back to the list
    else: # GET request
        form = TestForm(instance=test) # Populate form with existing data

    context = {
        'form': form,
        'test': test, # Pass the test object
        'is_edit': True, # Flag to indicate whether we're adding or editing
    }
    return render(request, 'quiz/custom_admin/test_form.html', context)


@user_passes_test(is_staff_check)
def custom_admin_delete_test(request, test_id):
    """ Delete a Test type """
    test = get_object_or_404(Test, id=test_id)

    if request.method == 'POST':
        test.delete()
        messages.success(request, f'Test "{test.name}" deleted successfully.')
        return redirect('custom_admin_tests') # Redirect back to the list

    # GET request for confirmation page (optional but recommended)
    context = {
        'test': test,
    }
    return render(request, 'quiz/custom_admin/test_confirm_delete.html', context)


@user_passes_test(is_staff_check)
def custom_admin_delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    # Prevent superuser from deleting themselves or other superusers without extra confirmation
    if user_to_delete.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only a superuser can delete another superuser.")
        return redirect('custom_admin_users')
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account from here.")
        return redirect('custom_admin_users')

    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, f"User '{user_to_delete.username}' deleted successfully.")
        return redirect('custom_admin_users')
    
    context = {'user_to_delete': user_to_delete}
    return render(request, 'quiz/custom_admin/user_confirm_delete.html', context)


@user_passes_test(is_staff_check)
def custom_admin_block_user(request, user_id):
    user_to_block = get_object_or_404(User, id=user_id)
    # Get or create UserProfile for the user
    # Note: UserProfile should automatically be created via signal, so .userprofile should exist
    user_profile = user_to_block.userprofile
    
    # Prevent blocking yourself or other superusers unless specific logic
    if user_to_block == request.user:
        messages.error(request, "You cannot block your own account.")
        return redirect('custom_admin_users')
    if user_to_block.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only a superuser can block another superuser.")
        return redirect('custom_admin_users')

    if request.method == 'POST':
        form = UserBlockForm(request.POST, instance=user_profile) # Target UserProfile instance
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user_to_block.username}' blocked until {user_profile.blocked_until}.")
            return redirect('custom_admin_users')
        else:
            # If form is invalid, re-render with errors
            messages.error(request, "Please correct the form errors.")
    else:
        form = UserBlockForm(instance=user_profile) # Pre-fill if already blocked

    context = {
        'user_to_block': user_to_block,
        'form': form,
        'now': timezone.now(), # Pass current time for template logic
    }
    return render(request, 'quiz/custom_admin/user_block_form.html', context)


@user_passes_test(is_staff_check)
def custom_admin_unblock_user(request, user_id):
    user_to_unblock = get_object_or_404(User, id=user_id)
    user_profile = user_to_unblock.userprofile
    if request.method == 'POST':
        user_profile.blocked_until = None # Set to None to unblock
        user_profile.save()
        messages.success(request, f"User '{user_to_unblock.username}' unblocked.")
        return redirect('custom_admin_users')
    messages.info(request, "Please confirm unblock via POST request.") # This message should only appear if somehow accessed via GET
    return redirect('custom_admin_users')


@user_passes_test(is_staff_check)
def custom_admin_toggle_staff(request, user_id):
    user_to_toggle = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Prevent staff from removing own staff status, or affecting superusers without specific logic
        if user_to_toggle == request.user and not request.user.is_superuser:
            messages.error(request, "You cannot change your own staff status from here unless you are a superuser.")
            return redirect('custom_admin_users')
        if user_to_toggle.is_superuser and not request.user.is_superuser:
            messages.error(request, "Only a superuser can change staff status of another superuser.")
            return redirect('custom_admin_users')

        user_to_toggle.is_staff = not user_to_toggle.is_staff
        user_to_toggle.save()
        status = "granted" if user_to_toggle.is_staff else "revoked"
        messages.success(request, f"Staff status for '{user_to_toggle.username}' has been {status}.")
        return redirect('custom_admin_users')
    # Fallback for GET request if someone tries to access directly
    messages.info(request, "User staff status can only be toggled via POST.")
    return redirect('custom_admin_users')


@user_passes_test(is_staff_check)
def custom_admin_toggle_superuser(request, user_id):
    user_to_toggle = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Superuser only can toggle other superusers, and cannot remove own superuser status easily
        if user_to_toggle == request.user:
            messages.error(request, "You cannot change your own superuser status from here.")
            return redirect('custom_admin_users')
        if not request.user.is_superuser:
            messages.error(request, "Only a superuser can change superuser status.")
            return redirect('custom_admin_users')

        user_to_toggle.is_superuser = not user_to_toggle.is_superuser
        user_to_toggle.save()
        status = "granted" if user_to_toggle.is_superuser else "revoked"
        messages.success(request, f"Superuser status for '{user_to_toggle.username}' has been {status}.")
        return redirect('custom_admin_users')
    # Fallback for GET request
    messages.info(request, "User superuser status can only be toggled via POST.")
    return redirect('custom_admin_users')