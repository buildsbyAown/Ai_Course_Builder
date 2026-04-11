from django.contrib import admin
from .models import Course, Week, Day, UserProgress

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration', 'level_has', 'level_required', 'language', 'created_at']
    list_filter = ['level_has', 'level_required', 'language', 'title']
    search_fields = ['title']

@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ['course', 'week_number', 'title']
    list_filter = ['course']
    ordering = ['course', 'week_number']

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ['week', 'day_number', 'title', 'video_url']
    list_filter = ['week__course']
    ordering = ['week', 'day_number']

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'current_week', 'current_day', 'is_completed', 'get_progress_percentage']
    list_filter = ['is_completed', 'course']
    search_fields = ['user__username', 'course__title']
    
    def get_progress_percentage(self, obj):
        return f"{obj.get_progress_percentage():.1f}%"
    get_progress_percentage.short_description = 'Progress'