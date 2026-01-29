from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.IntegerField()  # in months
    hours_per_day = models.IntegerField(default=2)
    level_has = models.CharField(max_length=100)
    level_required = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    outline = models.TextField()  # generated outline
    outline_score = models.IntegerField(default=0, help_text="Outline quality score (0-100)")
    is_predefined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Week(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.IntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        ordering = ['week_number']

    def __str__(self):
        return f"Week {self.week_number} - {self.course.title}"


class Day(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='days')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    video_thumbnail = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        return f"Day {self.day_number} - Week {self.week.week_number}"


# ---------- QUIZZES ----------

class Quiz(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    content = models.TextField()  # JSON or text representation of questions
    total_marks = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz - {self.title} (Week {self.week.week_number})"

class QuizSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'quiz']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"


# ---------- ASSIGNMENTS ----------

class Assignment(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_marks = models.IntegerField(default=100)
    content = models.TextField(blank=True, null=True)  # Optional detailed content
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment - {self.title} (Week {self.week.week_number})"


class AssignmentSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    submitted_text = models.TextField(blank=True, null=True)
    grade = models.FloatField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'assignment']

    def __str__(self):
        return f"{self.user.username} - {self.assignment.title}"


# ---------- USER PROGRESS ----------

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    current_week = models.IntegerField(default=1)
    current_day = models.IntegerField(default=1)
    completed_weeks = models.JSONField(default=list)
    completed_days = models.JSONField(default=list)
    completed_quizzes = models.JSONField(default=list)
    completed_assignments = models.JSONField(default=list)
    is_completed = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

    def get_progress_percentage(self):
        """Calculate overall course progress percentage (for entire course)"""
        # Count total days across all weeks
        total_days = sum(week.days.count() for week in self.course.weeks.all())
        total_quizzes = sum(week.quizzes.count() for week in self.course.weeks.all())
        total_assignments = sum(week.assignments.count() for week in self.course.weeks.all())

        completed_count = len(self.completed_days) + len(self.completed_quizzes) + len(self.completed_assignments)
        total_items = total_days + total_quizzes + total_assignments

        if total_items == 0:
            return 0
        return min(100, (completed_count / total_items) * 100)
    
    def get_week_progress_percentage(self, week):
        """Calculate progress for a specific week"""
        total_days = week.days.count()
        total_quizzes = week.quizzes.count()
        total_assignments = week.assignments.count()
        
        # Get all day IDs in this week
        week_day_ids = set(d.id for d in week.days.all())
        week_quiz_ids = set(q.id for q in week.quizzes.all())
        week_assignment_ids = set(a.id for a in week.assignments.all())
        
        # Count completed items in this week
        completed_days = sum(1 for day_id in self.completed_days if int(day_id) in week_day_ids)
        completed_quizzes = sum(1 for quiz_id in self.completed_quizzes if int(quiz_id) in week_quiz_ids)
        completed_assignments = sum(1 for assign_id in self.completed_assignments if int(assign_id) in week_assignment_ids)
        
        completed_count = completed_days + completed_quizzes + completed_assignments
        total_items = total_days + total_quizzes + total_assignments
        
        if total_items == 0:
            return 0
        return min(100, (completed_count / total_items) * 100)

class ChatbotConversation(models.Model):
    """Store chatbot conversations for each user per day"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    week_number = models.IntegerField()
    day_number = models.IntegerField()
    messages = models.JSONField(default=list)  # Store conversation history
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course', 'week_number', 'day_number']
    
    def __str__(self):
        return f"{self.user.username} - Week {self.week_number}, Day {self.day_number}"