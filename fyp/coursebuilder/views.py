from typing import List, Dict, Tuple
import math
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
import markdown
from groq import Groq
import requests
from urllib.parse import urlparse, parse_qs
from .models import *
from .schema.schema import InputSchema
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
# Add these imports at the top
import json
from django.views.decorators.http import require_http_methods
from django.utils import timezone

import logging
import os

def get_function_logger(func_name):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(func_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(f"{log_dir}/{func_name}.txt", mode="a")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent
OUTLINES_DIR = BASE_DIR / "outlines_txt"

def home(request):
    return render(request, "landing_page.html")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password)
        user.save()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login")

    return render(request, "register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

def logout_view(request):
    try:
        logout(request)
    except Exception:
        pass
    return render(request, "logout.html")

@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, "course_list.html", {"courses": courses})

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not UserProgress.objects.filter(user=request.user, course=course).exists():
        UserProgress.objects.create(user=request.user, course=course)
        messages.success(request, f"Enrolled in {course.title}")
    else:
        messages.info(request, "You are already enrolled in this course.")
    return redirect("dashboard")

# ---------- QUIZZES ----------

@login_required
def quiz_detail(request, course_id, week_number, quiz_id=None):
    """View for taking a quiz"""
    course = get_object_or_404(Course, id=course_id)
    week = get_object_or_404(Week, course=course, week_number=week_number)
    
    # If no quiz_id provided, get or create quiz for this week
    if quiz_id:
        quiz = get_object_or_404(Quiz, id=quiz_id, week=week)
    else:
        # Get or create quiz for this week
        quiz, created = Quiz.objects.get_or_create(
            week=week,
            defaults={
                'title': f'Week {week_number} Quiz',
                'content': generate_quiz_content(week.content, week_number),
                'total_marks': 10
            }
        )
    
    # Check if user has already submitted
    user_submission = QuizSubmission.objects.filter(
        user=request.user,
        quiz=quiz
    ).first()
    
    if request.method == 'POST':
        # Handle quiz submission
        score = calculate_quiz_score(request.POST, quiz.content)
        
        if user_submission:
            # Update existing submission
            user_submission.score = score
            user_submission.save()
        else:
            # Create new submission
            user_submission = QuizSubmission.objects.create(
                user=request.user,
                quiz=quiz,
                score=score
            )
            # Update user progress
            user_progress = get_object_or_404(UserProgress, user=request.user, course=course)
            if str(quiz.id) not in user_progress.completed_quizzes:
                user_progress.completed_quizzes.append(str(quiz.id))
                user_progress.save()
        
        return redirect('quiz_result', course_id=course_id, week_number=week_number, quiz_id=quiz.id)
    
    # Parse quiz content
    quiz_data = json.loads(quiz.content) if quiz.content else []
    
    return render(request, 'quiz_detail.html', {
        'course': course,
        'week': week,
        'quiz': quiz,
        'quiz_data': quiz_data,
        'user_submission': user_submission,
        'has_submitted': user_submission is not None
    })

def generate_quiz_content(week_content, week_number):
    """Generate quiz questions based on week content using AI"""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        prompt = f"""
        Based on the following week {week_number} content, create a quiz with exactly 5 multiple-choice questions.
        
        Week Content:
        {week_content}
        
        Format the response as a JSON array with this exact structure:
        [
            {{
                "question": "Question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "explanation": "Brief explanation of the correct answer"
            }},
            ... (4 more questions)
        ]
        
        Requirements:
        - Each question must have exactly 4 options
        - correct_answer must be 0, 1, 2, or 3 (index of correct option)
        - Questions should cover different topics from the week
        - Make questions challenging but fair
        - Include brief explanations for correct answers
        """
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        # Try to parse JSON from response
        content = response.choices[0].message.content
        # Clean the response to extract JSON
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            json_str = content[json_start:json_end]
            quiz_data = json.loads(json_str)
            
            # Validate structure
            if len(quiz_data) == 5:
                return json_str
                
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
    
    # Fallback quiz data
    return json.dumps([
        {
            "question": f"What is the main topic of Week {week_number}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "This is the correct answer because..."
        }
        for _ in range(5)
    ])

def calculate_quiz_score(form_data, quiz_content):
    """Calculate score for quiz submission"""
    try:
        quiz_data = json.loads(quiz_content)
        score = 0
        
        for i, question in enumerate(quiz_data):
            user_answer = form_data.get(f'question_{i}')
            if user_answer and int(user_answer) == question['correct_answer']:
                score += 2  # 2 marks per question for 5 questions = 10 total
        
        return score
    except Exception as e:
        print(f"Error calculating quiz score: {str(e)}")
        return 0

@login_required
def quiz_result(request, course_id, week_number, quiz_id):
    """View quiz results"""
    course = get_object_or_404(Course, id=course_id)
    week = get_object_or_404(Week, course=course, week_number=week_number)
    quiz = get_object_or_404(Quiz, id=quiz_id, week=week)
    
    user_submission = get_object_or_404(QuizSubmission, user=request.user, quiz=quiz)
    quiz_data = json.loads(quiz.content) if quiz.content else []
    
    return render(request, 'quiz_result.html', {
        'course': course,
        'week': week,
        'quiz': quiz,
        'user_submission': user_submission,
        'quiz_data': quiz_data,
        'score_percentage': (user_submission.score / quiz.total_marks) * 100
    })

# ---------- ASSIGNMENTS ----------

@login_required
def assignment_detail(request, course_id, week_number, assignment_id=None):
    """View for assignment"""
    course = get_object_or_404(Course, id=course_id)
    week = get_object_or_404(Week, course=course, week_number=week_number)
    
    # If no assignment_id provided, get or create assignment for this week
    if assignment_id:
        assignment = get_object_or_404(Assignment, id=assignment_id, week=week)
    else:
        # Get or create assignment for this week
        assignment, created = Assignment.objects.get_or_create(
            week=week,
            defaults={
                'title': f'Week {week_number} Assignment',
                'description': generate_assignment_description(week.content, week_number),
                'due_date': timezone.now() + timezone.timedelta(days=7),  # Due in 1 week
                'max_marks': 100
            }
        )
    
    user_submission = AssignmentSubmission.objects.filter(
        user=request.user,
        assignment=assignment
    ).first()
    
    if request.method == 'POST':
        # Handle assignment submission
        submitted_text = request.POST.get('submission_text', '')
        submitted_file = request.FILES.get('submission_file')
        
        if user_submission:
            # Update existing submission
            if submitted_file:
                user_submission.submitted_file = submitted_file
            user_submission.submitted_text = submitted_text
            user_submission.submitted_at = timezone.now()
            user_submission.save()
        else:
            # Create new submission
            user_submission = AssignmentSubmission.objects.create(
                user=request.user,
                assignment=assignment,
                submitted_file=submitted_file,
                submitted_text=submitted_text
            )
            # Update user progress
            user_progress = get_object_or_404(UserProgress, user=request.user, course=course)
            if str(assignment.id) not in user_progress.completed_assignments:
                user_progress.completed_assignments.append(str(assignment.id))
                user_progress.save()
        
        messages.success(request, "Assignment submitted successfully!")
        return redirect('assignment_detail', course_id=course_id, week_number=week_number, assignment_id=assignment.id)
    
    return render(request, 'assignment_detail.html', {
        'course': course,
        'week': week,
        'assignment': assignment,
        'user_submission': user_submission,
        'has_submitted': user_submission is not None
    })

def generate_assignment_description(week_content, week_number):
    """Generate assignment description based on week content"""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        prompt = f"""
        Based on the following week {week_number} content, create a practical assignment.
        
        Week Content:
        {week_content}
        
        Create an assignment description with:
        1. A clear, practical task that applies the week's concepts
        2. Something simple that can be done in 1-2 hours
        3. Clear instructions
        4. Expected outcomes
        
        Example: "Write a Python function that calculates the factorial of a number and test it with different inputs."
        
        Keep it concise and practical.
        """
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating assignment: {str(e)}")
    
    # Fallback assignment
    return f"Apply the concepts learned in Week {week_number} by completing a practical exercise related to the topics covered."

@login_required
def grade_assignment(request, submission_id):
    """For instructors to grade assignments"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission to grade assignments.")
        return redirect('dashboard')
    
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '')
        
        try:
            grade_value = float(grade)
            if 0 <= grade_value <= submission.assignment.max_marks:
                submission.grade = grade_value
                submission.graded_at = timezone.now()
                submission.save()
                messages.success(request, f"Assignment graded: {grade_value}/{submission.assignment.max_marks}")
            else:
                messages.error(request, f"Grade must be between 0 and {submission.assignment.max_marks}")
        except ValueError:
            messages.error(request, "Invalid grade value")
        
        return redirect('assignment_submissions', assignment_id=submission.assignment.id)
    
    return render(request, 'grade_assignment.html', {
        'submission': submission
    })

@login_required
def assignment_submissions(request, assignment_id):
    """View all submissions for an assignment (for instructors)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission to view submissions.")
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).select_related('user')
    
    return render(request, 'assignment_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })

def get_predefined_outlines():
    """Get all available predefined outlines from the outlines_txt folder"""
    outlines = {}
    
    if OUTLINES_DIR.exists():
        for file_path in OUTLINES_DIR.glob("*.txt"):
            # Extract course name from filename
            course_name = file_path.stem.replace("_", " ").title()
            
            # Read the outline content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                outlines[course_name] = content
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return outlines

def search_predefined_outline(course_title):
    """
    Search for a predefined outline that matches the course title.
    Uses strict matching to avoid false positives.
    """
    outlines = get_predefined_outlines()
    course_title_lower = course_title.lower().strip()
    
    # Check for exact match (case-insensitive)
    for outline_name in outlines.keys():
        if course_title_lower == outline_name.lower():
            return outline_name, outlines[outline_name]
    
    # Check for acronym match (e.g., "OOP" matches "Object Oriented Programming")
    # Only if the input is all uppercase or all capital letters
    if course_title.isupper() or (len(course_title) <= 5 and all(c.isupper() or c.isdigit() or c.isspace() for c in course_title)):
        for outline_name in outlines.keys():
            # Extract acronym from outline name
            acronym = ''.join([word[0] for word in outline_name.split() if word[0].isupper()])
            if course_title_lower == acronym.lower():
                return outline_name, outlines[outline_name]
    
    # No match found - return None so LLM will generate an outline
    return None, None

def split_weeks(content: str) -> dict:
    pattern = r"(Week\s*\d+)([\s\S]*?)(?=(Week\s*\d+)|$)"
    matches = re.findall(pattern, content, re.IGNORECASE)
    weeks = {}
    for match in matches:
        week_title = match[0].strip()
        week_content = match[1].strip()
        weeks[week_title] = week_content
    return weeks

def beautify_response(content: str) -> str:
    html_output = markdown.markdown(
        content,
        extensions=["extra", "nl2br", "sane_lists"]
    )
    return html_output

def get_youtube_thumbnail(video_url):
    """Extract YouTube thumbnail from video URL"""
    try:
        parsed_url = urlparse(video_url)
        video_id = None
        
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            if parsed_url.path == '/watch':
                video_id = parse_qs(parsed_url.query).get('v', [None])[0]
            elif parsed_url.path.startswith('/embed/'):
                video_id = parsed_url.path.split('/embed/')[1].split('?')[0]
            elif parsed_url.path.startswith('/v/'):
                video_id = parsed_url.path.split('/v/')[1].split('?')[0]
        elif parsed_url.hostname in ['www.youtu.be', 'youtu.be']:
            video_id = parsed_url.path[1:]
        
        if video_id:
            video_id = video_id.split('?')[0].split('#')[0].strip()
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            return thumbnail
        
        return None
        
    except Exception as e:
        print(f"Error in get_youtube_thumbnail: {e}")
        return None

def search_youtube_video(topic, course_title=None):
    """
    Search YouTube for a relevant educational video on the given topic
    Returns: (video_url, thumbnail_url) or (None, None) if no results
    """
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            print("YouTube API key not found")
            return None, None
        
        if course_title:
            search_query = f"{course_title} {topic} tutorial education learning course"
        else:
            search_query = f"{topic} tutorial education learning course"
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'maxResults': 1,
            'key': api_key,
            'videoDuration': 'medium',
            'relevanceLanguage': 'en',
            'videoEmbeddable': 'true',
            'videoSyndicated': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("Data in search_youtube_video: ", data)
        
        if data.get('items'):
            video_id = data['items'][0]['id']['videoId']
            watch_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = data['items'][0]['snippet']['thumbnails']['high']['url']
            
            print(f" Found YouTube video for topic: {topic}")
            return watch_url, thumbnail_url
        
        print(f"No YouTube results for topic: {topic}")
        return None, None
        
    except Exception as e:
        print(f"YouTube API error for topic '{topic}': {str(e)}")
        return None, None

def gen_outline(data, use_predefined=True):
    """
    Generate course outline. If use_predefined is True and a matching
    predefined outline exists, use it. Otherwise, generate a new one.
    """
    title = data.title
    logger = get_function_logger("gen_outline")
    # First check for predefined outline
    if use_predefined:
        matched_name, outline_content = search_predefined_outline(title)
        if outline_content:
            logger.info(f"Using predefined outline: {matched_name}")
            logger.debug(f"Predefined outline content: {outline_content}")
            return outline_content, matched_name, True  # True indicates predefined outline
    
    logger.info("No predefined outline found. Generating using LLM.")
    # If no predefined outline found, generate new one
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    level_has = data.level_has
    level_required = data.level_required
    duration = data.duration
    language = data.language
    hours_per_day = data.hours_per_day
    
    total_weeks = int(duration) * 4
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""
                
                Create an extremely detailed course outline for a course titled "{title}".  
                The course should be designed for learners with a "{level_has}" level of knowledge and aims to bring them to a "{level_required}" level.  
                The outline generated should be in "{language}" and will span approximately "{duration}" months ({total_weeks} weeks).  
                The student can study for {hours_per_day} hours per day.

                :zap: Important Instructions:
                - The total number of weeks = {duration} * 4 = {total_weeks}.  
                - Generate an outline that covers **all weeks without skipping**.  
                - Use clear headings in the exact format:  
                ## Week 1  
                ## Week 2  
                ... until ## Week {total_weeks}.  

                - For each week, provide **exactly 6 bullet points** (one for each day of the week, assuming one rest day).  
                - **CRITICAL**: Each day MUST have a specific, descriptive title related to the week's theme.
                - **DO NOT** use generic placeholders like "Introduction to [Topic]" where [Topic] is the week title.
                - **DO NOT** use generic titles like "Fundamentals", "Advanced Concepts", "Practical Exercise" without specific context.
                
                Example of GOOD output (Specific):
                ## Week 1
                - Day 1: List Creation and Indexing - Creating lists and accessing elements
                - Day 2: List Slicing and Stride - Extracting sub-lists
                - Day 3: List Methods (append, extend, pop) - Modifying lists
                - Day 4: List Comprehensions - Concise list creation
                - Day 5: Nested Lists and Matrix Operations - Working with multi-dimensional data
                - Day 6: List Practice Problems - Solving real-world list challenges

                Example of BAD output (Generic - DO NOT DO THIS):
                ## Week 1
                - Day 1: Introduction to Lists
                - Day 2: List Fundamentals
                - Day 3: Practical Exercise
                - Day 4: Advanced Concepts
                - Day 5: Real-world Application
                - Day 6: Review

                - Format the response in Markdown.  
                """,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
    )

    response = chat_completion.choices[0].message.content
    logger.info("Outline generated successfully")
    logger.debug(f"LLM response: {response}")
    return response, title, False  # False indicates AI-generated outline


def evaluate_outline(course_title, course_outline, target_level):
    """
    Evaluate the quality and relevance of a course outline using Groq API.
    Returns a score from 0-100.
    """
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        evaluation_prompt = f"""
        Evaluate the following course outline for "{course_title}" on how good and relevant it is to the topic.
        
        Course Title: {course_title}
        Target Level: {target_level}
        
        Course Outline:
        {course_outline}
        
        Evaluate based on these criteria:
        1. **Relevance** (25 points): How relevant is the content to the course title?
        2. **Comprehensiveness** (25 points): Does the outline cover the topic thoroughly?
        3. **Structure & Organization** (20 points): Is the progression logical and well-structured?
        4. **Learning Outcomes** (20 points): Are the objectives clear and achievable?
        5. **Practical Balance** (10 points): Does it balance theory with practical applications?
        
        Provide ONLY a single number from 0-100 representing the overall quality score.
        Do not include any explanation, just the number.
        """
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": evaluation_prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
        )
        
        score_text = response.choices[0].message.content.strip()
        score = int(''.join(filter(str.isdigit, score_text.split()[0])))
        score = max(0, min(100, score))
        
        return score
    except Exception as e:
        print(f"Error evaluating outline: {str(e)}")
        return 0


@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            title = course.title
            course.delete()
            messages.success(request, f"Course '{title}' has been deleted.")
            return redirect('dashboard')
        messages.error(request, 'Invalid request method for deleting a course.')
        return redirect('dashboard')

    if request.method == 'POST':
        user_progress = UserProgress.objects.filter(user=request.user, course=course).first()
        if user_progress:
            user_progress.delete()
            messages.success(request, f"You have been unenrolled from '{course.title}'.")
            return redirect('dashboard')
        else:
            messages.error(request, "You are not enrolled in this course.")
            return redirect('dashboard')

    messages.error(request, 'Invalid request method for this action.')
    return redirect('dashboard')

def get_daily_detail(week_number, day_number, topic, hours_per_day, course_title):
    """
    Generate rich, non-repetitive, detailed daily content for a specific topic.
    Includes examples, exercises, YouTube resources, and structure variety.
    """
    import random
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


    prompt = f"""
    Generate a {hours_per_day}-hour detailed learning content for Week {week_number}, Day {day_number} of the course "{course_title}".
    The topic of the day is: "{topic}".
    
    Output in **Markdown** using this exact structure:

    ## Day {day_number}: {topic}
    **Learning Objectives:**
    - [3–5 concise, actionable goals]

    **Theory (≈30%)**
    Explain the core concepts clearly and progressively. Explain in lengthy detail.

    **Practical (≈50%)**
    Include coding examples, problem-solving tasks, that I can solve to get hands-on practice.
    Mention specific tools or libraries if applicable.

    **Review (≈20%)**
    - Key takeaways
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.6,
    )
    print("Response in get_daily_detail: ", response.choices[0].message.content)

    return response.choices[0].message.content

def get_weekly_detail(week_content, week_number, hours_per_day):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""
                You are an expert instructor designing a professional-grade learning experience.

                Create a **STRICTLY FORMATTED**, **IN-DEPTH**, and **NON-REPETITIVE** 6-day learning plan for:

                Week {week_number}
                Weekly Topics: {week_content}
                Daily Study Time: {hours_per_day} hours

                ================================
                🚨 ABSOLUTE FORMAT RULES (MANDATORY)
                ================================

                1. You MUST generate EXACTLY **6 days** (Day 1 to Day 6).
                2. Each day MUST follow THIS FORMAT EXACTLY — no extra headings, notes, or summaries:

                ## Day X: <Exact topic name being taught that day>
                **Video Resource:** <Relevant YouTube educational URL OR "No video">
                **Content:**
                <DETAILED CONTENT>

                ❌ OUTPUT IS INVALID IF:
                - Any day is missing
                - Any heading format changes
                - Any required line is missing
                - Any extra section is added

                ================================
                🎯 CONTENT QUALITY REQUIREMENTS
                ================================

                For EACH day:
                - The day title MUST be the **specific topic or concept covered**, not generic labels
                - The content MUST implicitly include:
                • Learning goals  
                • Conceptual explanation  
                • Concrete examples  
                • Hands-on or thinking-based exercises  
                • Real-world or industry context  

                ⚠️ IMPORTANT:
                - DO NOT include headings like:
                "Learning Objectives", "Theory", "Examples", "Exercises", etc.
                - These are ONLY guidance for you — they must NOT appear in the output.

                ================================
                🔄 NON-REPETITION REQUIREMENT
                ================================

                - Each day MUST use a **different internal structure**
                - Vary:
                - Teaching style (explanation-first, example-first, problem-first, scenario-based, etc.)
                - Types of exercises (coding task, analysis, design challenge, debugging, reflection, mini-project)
                - Examples and contexts
                - Avoid repeating sentence patterns across days

                ================================
                🚫 FORBIDDEN DAY TITLES
                ================================

                DO NOT use:
                - Introduction to...
                - Basics / Fundamentals
                - Advanced Concepts
                - Practice Session
                - Review
                - Hands-on Practice

                Each title MUST clearly name the **actual concept, tool, or workflow** being studied.

                ================================
                📈 PROGRESSION RULES
                ================================

                - Days must build logically on previous days
                - Complexity should gradually increase
                - Content must align tightly with the weekly topics

                ================================
                🔍 FINAL SELF-CHECK (REQUIRED)
                ================================

                Before responding, silently verify:
                - Exactly 6 days are present
                - Format is followed EXACTLY
                - No forbidden headings or generic titles appear
                - Each day feels distinct in structure and approach
                - Content realistically fills {hours_per_day} hours/day

                If ANY rule is violated, FIX IT before outputting.

                Respond in **Markdown only**.
                """,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )

    response = chat_completion.choices[0].message.content
    print(f"Week {week_number} generated content:")
    print("Response in get_weekly_detail: ", response)
    return response

def parse_daily_content(weekly_detail):
    """Parse the weekly detail into individual days with video URLs"""
    days = []
    
    day_pattern = r"## Day\s*(\d+):\s*([^\n]+)(?:\n\*\*Video Resource:\*\*\s*([^\n]*))?(?:\n\*\*Content:\*\*\s*([\s\S]*?))(?=## Day\s*\d+:|$)"
    
    matches = re.findall(day_pattern, weekly_detail, re.IGNORECASE)
    
    print(f"Found {len(matches)} days in weekly detail")
    
    for match in matches:
        try:
            day_number = int(match[0])
            title = match[1].strip()
            video_url = match[2].strip() if match[2] and match[2].strip() not in ["", "No video", "[No video]"] else ""
            content = match[3].strip() if match[3] else "Content not available"
            
            content = re.sub(r'\*\*|\*|`', '', content)
            
            if video_url and ('youtube.com/watch?v=' in video_url or 'youtu.be/' in video_url):
                if 'youtube.com/watch?v=' in video_url:
                    video_id = video_url.split('youtube.com/watch?v=')[1].split('&')[0]
                    video_url = f'https://www.youtube.com/embed/{video_id}'
                elif 'youtu.be/' in video_url:
                    video_id = video_url.split('youtu.be/')[1].split('?')[0]
                    video_url = f'https://www.youtube.com/embed/{video_id}'
            
            video_thumbnail = get_youtube_thumbnail(video_url) if video_url else ""
            
            days.append({
                'day_number': day_number,
                'title': title,
                'video_url': video_url,
                'video_thumbnail': video_thumbnail,
                'content': content
            })
            
            print(f"Parsed Day {day_number}: {title}")
            
        except Exception as e:
            print(f"Error parsing day: {e}")
            continue
    
    if not days:
        days = alternative_parse_daily_content(weekly_detail)
    
    return days

def alternative_parse_daily_content(weekly_detail):
    """Alternative parsing method if the main one fails"""
    days = []
    
    day_sections = re.split(r'## Day\s*\d+:', weekly_detail)
    
    for i, section in enumerate(day_sections[1:], 1):
        try:
            lines = section.strip().split('\n')
            title = lines[0].strip() if lines else f"Day {i} Content"
            
            video_url = ""
            content_lines = []
            
            for line in lines:
                if 'youtube.com' in line or 'youtu.be' in line:
                    url_match = re.search(r'(https?://[^\s]+)', line)
                    if url_match:
                        video_url = url_match.group(1)
                elif line.strip() and not line.startswith('**'):
                    content_lines.append(line.strip())
            
            content = '\n\n'.join(content_lines) if content_lines else "Detailed content for this day."
            
            if video_url and ('youtube.com/watch?v=' in video_url or 'youtu.be/' in video_url):
                if 'youtube.com/watch?v=' in video_url:
                    video_id = video_url.split('youtube.com/watch?v=')[1].split('&')[0]
                    video_url = f'https://www.youtube.com/embed/{video_id}'
                elif 'youtu.be/' in video_url:
                    video_id = video_url.split('youtu.be/')[1].split('?')[0]
                    video_url = f'https://www.youtube.com/embed/{video_id}'
            
            video_thumbnail = get_youtube_thumbnail(video_url) if video_url else ""
            
            days.append({
                'day_number': i,
                'title': title,
                'video_url': video_url,
                'video_thumbnail': video_thumbnail,
                'content': content
            })
            
        except Exception as e:
            print(f"Error in alternative parsing for day {i}: {e}")
            continue
    
    return days

def create_fallback_days(week_content, week_number, hours_per_day):
    """Create fallback day content when AI generation fails"""
    days = []
    topics = week_content.split('\n')[:6]
    
    for i in range(1, 7):
        topic = topics[i-1].replace('-', '').strip() if i-1 < len(topics) else f"Week {week_number} Topic {i}"
        
        days.append({
            'day_number': i,
            'title': f"Day {i}: {topic}",
            'video_url': "",
            'video_thumbnail': "",
            'content': f"""
            <h5>Learning Objectives</h5>
            <ul>
                <li>Understand the key concepts of {topic}</li>
                <li>Apply {topic} in practical scenarios</li>
                <li>Complete exercises to reinforce learning</li>
            </ul>
            
            <h5>Study Plan ({hours_per_day} hours)</h5>
            <ol>
                <li><strong>30 minutes:</strong> Review theoretical concepts</li>
                <li><strong>45 minutes:</strong> Work through examples and case studies</li>
                <li><strong>45 minutes:</strong> Complete practical exercises</li>
            </ol>
            
            <h5>Key Concepts</h5>
            <p>Today we'll focus on mastering {topic}. This includes understanding the fundamental principles and learning how to apply them in real-world scenarios.</p>
            
            <h5>Practical Exercise</h5>
            <p>Create a small project or complete exercises that demonstrate your understanding of {topic}.</p>
            
            <h5>Additional Resources</h5>
            <ul>
                <li>Review the course materials</li>
                <li>Practice with online exercises</li>
                <li>Join discussion forums for help</li>
            </ul>
            """
        })
    
    return days

@login_required
def course_input(request):
    """Handle course creation with predefined outline support"""
    
    # Get available outlines for autocomplete
    outlines = get_predefined_outlines()
    outline_names = list(outlines.keys())
    
    if request.method == "POST":
        title = request.POST.get("title")
        duration = request.POST.get("duration")
        hours_per_day = request.POST.get("hours_per_day", 2)
        level_has = request.POST.get("level_has")
        level_required = request.POST.get("level_required")
        language = request.POST.get("language")
        use_predefined = request.POST.get("use_predefined", "true") == "true"
        show_outline = request.POST.get("show_outline", "false") == "true"
        
        try:
            data = InputSchema(
                title=title,
                duration=duration,
                hours_per_day=hours_per_day,
                level_has=level_has,
                level_required=level_required,
                language=language
            )
            
            # If just showing outline, render it without creating course
            if show_outline:
                outline, matched_name, is_predefined = gen_outline(data, use_predefined)
                
                # Beautify the outline for display
                html_outline = beautify_response(outline)
                
                return render(request, "course_preview.html", {
                    'title': title,
                    'matched_name': matched_name if is_predefined else title,
                    'outline': html_outline,
                    'is_predefined': is_predefined,
                    'duration': duration,
                    'hours_per_day': hours_per_day,
                    'level_has': level_has,
                    'level_required': level_required,
                    'language': language,
                    'form_data': {
                        'title': title,
                        'duration': duration,
                        'hours_per_day': hours_per_day,
                        'level_has': level_has,
                        'level_required': level_required,
                        'language': language,
                        'use_predefined': use_predefined
                    }
                })
            
            # Generate or get outline
            outline, matched_name, is_predefined = gen_outline(data, use_predefined)
            weeks_content = split_weeks(outline)
            
            # Evaluate outline quality
            outline_score = evaluate_outline(title, outline, level_required)
            
            # Save course to database
            course = Course.objects.create(
                title=matched_name if is_predefined else title,
                duration=duration,
                hours_per_day=hours_per_day,
                level_has=level_has,
                level_required=level_required,
                language=language,
                outline=outline,
                outline_score=outline_score,
                is_predefined=is_predefined
            )
            
            # Create week objects
            for week_title, week_content in weeks_content.items():
                week_number_match = re.search(r'\d+', week_title)
                if week_number_match:
                    week_number = int(week_number_match.group())
                    Week.objects.create(
                        course=course,
                        week_number=week_number,
                        title=week_title,
                        content=week_content
                    )
            
            # Enroll user in the course
            UserProgress.objects.create(
                user=request.user,
                course=course,
                current_week=1,
                current_day=1
            )
            
            messages.success(request, f"Course '{course.title}' created successfully!")
            if is_predefined:
                messages.info(request, "✓ Used predefined outline")
            return redirect('course_detail', course_id=course.id)
        
        except Exception as e:
            messages.error(request, f"Error creating course: {str(e)}")
            return redirect('course_create')
    
    return render(request, "course_form.html", {
        'outline_names': outline_names,
        'outlines_json': json.dumps(outline_names)
    })

@login_required
def dashboard(request):
    user_progress = UserProgress.objects.filter(user=request.user).select_related('course')
    
    progress_data = []
    total_courses = user_progress.count()
    completed_courses = 0
    total_progress = 0
    incomplete_count = 0
    
    for progress in user_progress:
        progress_percentage = progress.get_progress_percentage()
        progress_data.append({
            'course': progress.course,
            'progress': progress_percentage,
            'current_week': progress.current_week,
            'current_day': progress.current_day,
            'is_completed': progress.is_completed
        })
        
        if progress.is_completed:
            completed_courses += 1
        else:
            incomplete_count += 1
            total_progress += progress_percentage
    
    average_progress = total_progress / incomplete_count if incomplete_count > 0 else 0

    total_hours_learned = 0
    for progress in user_progress:
        try:
            completed_days = progress.completed_days or []
            days_count = len(completed_days)
            hours_per_day = getattr(progress.course, 'hours_per_day', 0) or 0
            total_hours_learned += days_count * int(hours_per_day)
        except Exception:
            continue
    
    return render(request, 'dashboard.html', {
        'progress_data': progress_data,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'average_progress': average_progress,
        'hours_learned_total': total_hours_learned
    })

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_progress = get_object_or_404(UserProgress, user=request.user, course=course)
    weeks = course.weeks.all().order_by('week_number')
    
    user_name = request.user.get_full_name() or request.user.username or 'User'
    
    try:
        course_completed_days = user_progress.completed_days or []
        course_hours_learned = len(course_completed_days) * (int(course.hours_per_day) if course.hours_per_day else 0)
    except Exception:
        course_hours_learned = 0

    all_user_progress = UserProgress.objects.filter(user=request.user).select_related('course')
    total_hours_learned = 0
    for up in all_user_progress:
        try:
            cdays = up.completed_days or []
            hrs = int(getattr(up.course, 'hours_per_day', 0) or 0)
            total_hours_learned += len(cdays) * hrs
        except Exception:
            continue

    return render(request, 'course_detail.html', {
        'course': course,
        'user_progress': user_progress,
        'weeks': weeks,
        'user_name': user_name,
        'course_hours_learned': course_hours_learned,
        'hours_learned_total': total_hours_learned,
    })

@login_required
def profile_view(request):
    """Allow user to update username and password."""
    user = request.user

    if request.method == 'POST':
        if 'update_username' in request.POST:
            new_username = request.POST.get('new_username', '').strip()
            if not new_username:
                messages.error(request, 'Username cannot be empty.')
                return redirect('profile')
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, 'This username is already taken.')
                return redirect('profile')
            user.username = new_username
            user.save()
            messages.success(request, 'Username updated successfully.')
            return redirect('profile')

        if 'update_password' in request.POST:
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('profile')
            if new_password != confirm_password:
                messages.error(request, 'New password and confirmation do not match.')
                return redirect('profile')
            if len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters.')
                return redirect('profile')

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
            return redirect('profile')

    return render(request, 'profile.html', {'user': user})

from concurrent.futures import ThreadPoolExecutor, as_completed

@login_required
def week_detail(request, course_id, week_number):
    course = get_object_or_404(Course, id=course_id)
    week = get_object_or_404(Week, course=course, week_number=week_number)
    user_progress = get_object_or_404(UserProgress, user=request.user, course=course)
    
    # Get the current day from user progress or default to day 1
    current_day = user_progress.current_day
    
    # Try to get the specific day object
    try:
        current_day_obj = Day.objects.get(week=week, day_number=current_day)
    except Day.DoesNotExist:
        # If day doesn't exist, use the first available day or None
        current_day_obj = week.days.order_by('day_number').first()
    
    # Get or create quiz for this week
    quiz, quiz_created = Quiz.objects.get_or_create(
        week=week,
        defaults={
            'title': f'Week {week_number} Quiz',
            'content': generate_quiz_content(week.content, week_number),
            'total_marks': 10
        }
    )
    
    # Get or create assignment for this week
    assignment, assignment_created = Assignment.objects.get_or_create(
        week=week,
        defaults={
            'title': f'Week {week_number} Assignment',
            'description': generate_assignment_description(week.content, week_number),
            'due_date': timezone.now() + timezone.timedelta(days=7),
            'max_marks': 100
        }
    )
    
    # Check user submissions
    quiz_submission = QuizSubmission.objects.filter(user=request.user, quiz=quiz).first()
    assignment_submission = AssignmentSubmission.objects.filter(
        user=request.user, 
        assignment=assignment
    ).first()
    
    # Generate/update day content if they have placeholder content
    # Check if any day still has the placeholder content
    has_placeholder_content = week.days.filter(
        content="Content will be loaded when you view this day."
    ).exists()
    
    if has_placeholder_content or not week.days.exists():
        try:
            # First, try to extract topics from bullet points
            topics = [line.strip("- ").strip() for line in week.content.split("\n") if line.strip().startswith("-")]
            
            # If we don't have enough topics, split the content and extract meaningful sections
            if len(topics) < 5:
                # Try to get the first few lines that look like topics (any non-empty line)
                lines = week.content.split("\n")
                topics = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and len(line) > 5:
                        # Remove common markdown symbols and clean up
                        clean_line = line.lstrip("- •*").strip()
                        if clean_line and clean_line not in topics:
                            topics.append(clean_line)
                    if len(topics) >= 6:
                        break
            
            # Ensure we have at least 5-6 topics (use generic ones if needed)
            default_topics = [
                "Introduction and Fundamentals",
                "Core Concepts and Theory",
                "Practical Applications",
                "Advanced Techniques",
                "Project Work and Review",
                "Assessment and Reflection"
            ]
            
            while len(topics) < 5:
                if len(topics) < len(default_topics):
                    topics.append(default_topics[len(topics)])
                else:
                    topics.append(f"Topic {len(topics) + 1}")
            
            topics = topics[:6]  # Limit to 6 days
            
            def generate_day(day_number, topic):
                daily_content = get_daily_detail(week_number, day_number, topic, course.hours_per_day, course.title)
                
                video_url, video_thumbnail = search_youtube_video(topic, course.title)
                
                content_html = markdown.markdown(daily_content, extensions=["extra", "nl2br", "sane_lists"])
                
                return {
                    "day_number": day_number,
                    "title": f"Day {day_number}: {topic}",
                    "content": content_html,
                    "video_url": video_url or "",
                    "video_thumbnail": video_thumbnail or "",
                }

            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [executor.submit(generate_day, i+1, topic) for i, topic in enumerate(topics)]
                for future in as_completed(futures):
                    day_data = future.result()
                    Day.objects.update_or_create(
                        week=week,
                        day_number=day_data['day_number'],
                        defaults={
                            'title': day_data['title'],
                            'content': day_data['content'],
                            'video_url': day_data['video_url'],
                            'video_thumbnail': day_data['video_thumbnail']
                        }
                    )
                    
        except Exception as e:
            messages.error(request, f"Error generating daily content: {str(e)}")
            days_data = create_fallback_days(week.content, week_number, course.hours_per_day)
            for day_data in days_data:
                Day.objects.update_or_create(
                    week=week,
                    day_number=day_data['day_number'],
                    defaults={
                        'title': day_data['title'],
                        'content': day_data['content'],
                        'video_url': day_data['video_url'],
                        'video_thumbnail': day_data['video_thumbnail']
                    }
                )
    
    # Get all days for the week
    days = week.days.all().order_by('day_number')
    
    # If current_day_obj is still None and we have days, use the first day
    if not current_day_obj and days.exists():
        current_day_obj = days.first()
    
    # Create a simple dictionary for the day if it doesn't exist
    if not current_day_obj:
        current_day_obj = {
            'day_number': current_day,
            'title': f'Day {current_day}',
            'content': 'Content for this day is being prepared.',
            'video_url': '',
            'video_thumbnail': '',
            'id': 0  # Dummy ID for the template
        }
    
    return render(request, 'week_detail.html', {
        'course': course,
        'week': week,
        'day': current_day_obj,  # Pass the day object/dict
        'days': days,
        'user_progress': user_progress,
        'week_progress_percentage': user_progress.get_week_progress_percentage(week),
        'quiz': quiz,
        'assignment': assignment,
        'quiz_submission': quiz_submission,
        'assignment_submission': assignment_submission
    })
    
    
@login_required
@csrf_exempt
def update_progress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            day_id = data.get('day_id')
            
            course = get_object_or_404(Course, id=course_id)
            day = get_object_or_404(Day, id=day_id)
            user_progress = get_object_or_404(UserProgress, user=request.user, course=course)
            
            if str(day_id) not in user_progress.completed_days:
                user_progress.completed_days.append(str(day_id))
            
            user_progress.current_week = day.week.week_number
            user_progress.current_day = day.day_number
            
            total_days = course.weeks.count() * 6
            if len(user_progress.completed_days) >= total_days:
                user_progress.is_completed = True
            
            user_progress.save()
            
            return JsonResponse({
                'success': True,
                'progress_percentage': user_progress.get_progress_percentage()
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})

@csrf_exempt
def search_courses(request):
    """API endpoint for course search/autocomplete"""
    if request.method == 'GET':
        query = request.GET.get('q', '').lower().strip()
        outlines = get_predefined_outlines()
        
        results = []
        
        for outline_name in outlines.keys():
            outline_name_lower = outline_name.lower()
            
            # Exact match
            if query == outline_name_lower:
                results.append({
                    'name': outline_name,
                    'match_type': 'exact'
                })
                continue
            
            # Acronym match
            acronym = ''.join([word[0] for word in outline_name.split() if word[0].isupper()])
            if query == acronym.lower():
                results.append({
                    'name': outline_name,
                    'match_type': 'acronym'
                })
                continue
            
            # Partial match
            if query in outline_name_lower:
                results.append({
                    'name': outline_name,
                    'match_type': 'partial'
                })
                continue
            
            # Word match
            query_words = query.split()
            outline_words = outline_name_lower.split()
            
            for q_word in query_words:
                if any(q_word in o_word or o_word in q_word for o_word in outline_words):
                    results.append({
                        'name': outline_name,
                        'match_type': 'word'
                    })
                    break
        
        # Limit results
        results = results[:10]
        
        return JsonResponse({
            'results': results,
            'count': len(results)
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# ---------- CHATBOT ----------

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chatbot_send_message(request):
    """Handle chatbot messages with week/day context"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        course_id = data.get('course_id')
        week_number = data.get('week_number')
        day_number = data.get('day_number')
        
        if not message:
            return JsonResponse({'success': False, 'error': 'Message is required'})
        
        # Get course and validate
        course = get_object_or_404(Course, id=course_id)
        week = get_object_or_404(Week, course=course, week_number=week_number)
        day = get_object_or_404(Day, week=week, day_number=day_number)
        
        # Get or create conversation
        conversation, created = ChatbotConversation.objects.get_or_create(
            user=request.user,
            course=course,
            week_number=week_number,
            day_number=day_number,
            defaults={'messages': []}
        )
        
        # Add user message to conversation
        conversation.messages.append({
            'role': 'user',
            'content': message,
            'timestamp': timezone.now().isoformat()
        })
        
        # Prepare context for AI
        context = f"""
        Week: {week_number}
        Day: {day_number}
        Course: {course.title}
        Day Topic: {day.title}
        Week Content: {week.content[:500]}...
        Day Content: {day.content[:500]}...
        
        The student is currently studying Week {week_number}, Day {day_number} of the course "{course.title}".
        Today's topic is: "{day.title}".
        
        Please provide helpful guidance specific to this day's content.
        """
        
        # Call Groq API with context
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Prepare conversation history for AI
        ai_messages = [
            {
                "role": "system",
                "content": f"""You are a helpful learning assistant for an online course platform. 
                You are currently helping a student with Week {week_number}, Day {day_number} of the course: "{course.title}".
                Today's specific topic is: "{day.title}".
                
                Guidelines:
                1. Be specific to today's learning material
                2. Provide practical help related to the day's topic
                3. Encourage and motivate the student
                4. If the question is not related to the course, politely redirect to course topics
                5. Keep responses concise but helpful
                6. Use examples from the course content when possible
                """
            }
        ]
        
        # Add recent conversation history (last 5 messages)
        recent_messages = conversation.messages[-10:]  # Last 10 messages for context
        for msg in recent_messages:
            ai_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Add current user message
        ai_messages.append({
            "role": "user",
            "content": f"Context: {context}\n\nStudent's question: {message}"
        })
        
        # Get AI response
        response = client.chat.completions.create(
            messages=ai_messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to conversation
        conversation.messages.append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': timezone.now().isoformat()
        })
        
        # Save conversation
        conversation.save()
        
        # Beautify the response
        html_response = markdown.markdown(
            ai_response,
            extensions=["extra", "nl2br", "sane_lists"]
        )
        
        return JsonResponse({
            'success': True,
            'response': html_response,
            'message_count': len(conversation.messages)
        })
        
    except Exception as e:
        print(f"Chatbot error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
def chatbot_get_conversation(request):
    """Get chatbot conversation for a specific day"""
    try:
        course_id = request.GET.get('course_id')
        week_number = request.GET.get('week_number')
        day_number = request.GET.get('day_number')
        
        if not all([course_id, week_number, day_number]):
            return JsonResponse({'success': False, 'error': 'Missing parameters'})
        
        conversation = ChatbotConversation.objects.filter(
            user=request.user,
            course_id=course_id,
            week_number=week_number,
            day_number=day_number
        ).first()
        
        messages = conversation.messages if conversation else []
        
        # Format messages with HTML
        formatted_messages = []
        for msg in messages:
            if msg['role'] == 'assistant':
                content = markdown.markdown(
                    msg['content'],
                    extensions=["extra", "nl2br", "sane_lists"]
                )
            else:
                content = msg['content']
            
            formatted_messages.append({
                'role': msg['role'],
                'content': content,
                'timestamp': msg.get('timestamp', '')
            })
        
        return JsonResponse({
            'success': True,
            'messages': formatted_messages,
            'has_conversation': conversation is not None
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
def chatbot_clear_conversation(request):
    """Clear chatbot conversation for a specific day"""
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        week_number = data.get('week_number')
        day_number = data.get('day_number')
        
        ChatbotConversation.objects.filter(
            user=request.user,
            course_id=course_id,
            week_number=week_number,
            day_number=day_number
        ).delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})