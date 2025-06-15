from django.urls import path
from . import views
from .views import (
    # Authentication View
    signup_view,

    # Test Views (User Facing)
    test_list, start_test, take_question, finish_test, test_results,

    # Custom Admin Views (Questions)
    custom_admin_questions, custom_admin_add_question, custom_admin_edit_question, custom_admin_delete_question,

    # Custom Admin Views (Tests)
    custom_admin_tests, custom_admin_add_test, custom_admin_edit_test, custom_admin_delete_test,

    # Custom Admin Views (Users) - New and existing imports for user management
    custom_admin_users,
    custom_admin_delete_user, custom_admin_block_user, custom_admin_unblock_user,
    custom_admin_toggle_staff, custom_admin_toggle_superuser,
)


urlpatterns = [
    # Authentication URL (only our custom signup view here)
    path('signup/', signup_view, name='signup'),
    # Django's default login/logout/password reset URLs are handled by
    # 'path('accounts/', include('django.contrib.auth.urls'))' in quiz_project/urls.py

    # Test Views (User Facing)
    path('tests/', test_list, name='test_list'),
    path('tests/start/<int:test_id>/', start_test, name='start_test'),
    path('tests/take/<int:attempt_id>/<int:question_index>/', take_question, name='take_question'),
    path('tests/finish/<int:attempt_id>/', finish_test, name='finish_test'),
    path('tests/results/<int:attempt_id>/', test_results, name='test_results'),

    # Custom Admin Views (Questions)
    # Existing URL for ALL questions
    path('admin/questions/', custom_admin_questions, name='custom_admin_questions'),
    # NEW URL for questions specific to a Test
    path('admin/tests/<int:test_id>/questions/', custom_admin_questions, name='custom_admin_test_questions'),

    # Existing URL for adding a question (can be generic or test-specific via query param)
    path('admin/questions/add/', custom_admin_add_question, name='custom_admin_add_question'),
    # NEW URL for adding a question directly to a specific Test
    path('admin/tests/<int:test_id>/questions/add/', custom_admin_add_question, name='custom_admin_add_question_to_test'),

    path('admin/questions/edit/<int:question_id>/', custom_admin_edit_question, name='custom_admin_edit_question'),
    path('admin/questions/delete/<int:question_id>/', custom_admin_delete_question, name='custom_admin_delete_question'),

    # Custom Admin Views (Tests)
    path('admin/tests/', custom_admin_tests, name='custom_admin_tests'),
    path('admin/tests/add/', custom_admin_add_test, name='custom_admin_add_test'),
    path('admin/tests/edit/<int:test_id>/', custom_admin_edit_test, name='custom_admin_edit_test'),
    path('admin/tests/delete/<int:test_id>/', custom_admin_delete_test, name='custom_admin_delete_test'),

    # Custom Admin Views (Users) - Existing and NEW URLs for management actions
    path('admin/users/', custom_admin_users, name='custom_admin_users'),
    path('admin/users/delete/<int:user_id>/', custom_admin_delete_user, name='custom_admin_delete_user'),
    path('admin/users/block/<int:user_id>/', custom_admin_block_user, name='custom_admin_block_user'),
    path('admin/users/unblock/<int:user_id>/', custom_admin_unblock_user, name='custom_admin_unblock_user'),
    path('admin/users/toggle-staff/<int:user_id>/', custom_admin_toggle_staff, name='custom_admin_toggle_staff'),
    path('admin/users/toggle-superuser/<int:user_id>/', custom_admin_toggle_superuser, name='custom_admin_toggle_superuser'),
]