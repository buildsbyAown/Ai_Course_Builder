from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('courses/', views.course_list, name='course_list'),
    path('course/create/', views.course_input, name='course_create'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/delete/', views.delete_course, name='course_delete'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:course_id>/week/<int:week_number>/', views.week_detail, name='week_detail'),

    path('update-progress/', views.update_progress, name='update_progress'),
    path('search-courses/', views.search_courses, name='search_courses'),  # New endpoint
    # Quiz URLs - FIXED: Different names for with and without quiz_id
    path('course/<int:course_id>/week/<int:week_number>/quiz/<int:quiz_id>/',
         views.quiz_detail, name='quiz_detail'),
    path('course/<int:course_id>/week/<int:week_number>/quiz/<int:quiz_id>/result/',
         views.quiz_result, name='quiz_result'),
    path('course/<int:course_id>/week/<int:week_number>/quiz/<int:quiz_id>/',
         views.quiz_detail, name='quiz_detail_with_id'),
    
    # Assignment URLs - FIXED: Different names for with and without assignment_id
    path('course/<int:course_id>/week/<int:week_number>/assignment/<int:assignment_id>/',
         views.assignment_detail, name='assignment_detail'),
    path('course/<int:course_id>/week/<int:week_number>/assignment/<int:assignment_id>/',
         views.assignment_detail, name='assignment_detail_with_id'),
    path('assignment/<int:submission_id>/grade/',
         views.grade_assignment, name='grade_assignment'),
    path('assignment/<int:assignment_id>/submissions/',
         views.assignment_submissions, name='assignment_submissions'),
    
    # Add to urlpatterns in urls.py
     path('chatbot/send/', views.chatbot_send_message, name='chatbot_send'),
     path('chatbot/conversation/', views.chatbot_get_conversation, name='chatbot_conversation'),
     path('chatbot/clear/', views.chatbot_clear_conversation, name='chatbot_clear'),
]