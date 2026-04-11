# Application Workflow Sheet: AI Course Builder

This document outlines the full detailed workflow of the application, starting from user authentication to course execution. It maps the user journey to specific URLs, `views.py` functions, and rendered templates.

## 1. Landing Page & Authentication

### 1.1 Home / Landing
- **URL:** `/`
- **View Function:** `home(request)`
- **Template:** `landing_page.html`
- **Description:** Unauthenticated or first-time users land here to understand the platform's value proposition.

### 1.2 User Registration
- **URL:** `/register/`
- **View Function:** `register_view(request)`
- **Template:** `register.html`
- **Workflow:**
  - **GET Request:** Renders the registration form.
  - **POST Request:** Submits username, password, and confirm password. If successful, creates the user and redirects to the **Login** page.

### 1.3 User Login
- **URL:** `/login/`, `/accounts/login/`
- **View Function:** `login_view(request)` or Django's `auth_views.LoginView` (in `fyp/urls.py`)
- **Template:** `login.html`
- **Workflow:**
  - **GET Request:** Renders the login form.
  - **POST Request:** Authenticates credentials. On success, logs the user in and redirects them to the **Dashboard**.

### 1.4 User Logout
- **URL:** `/logout/`, `/accounts/logout/`
- **View Function:** `logout_view(request)`
- **Template:** `logout.html`
- **Description:** Terminates the user's session.

---

## 2. Main Platform (Post-Login)

### 2.1 User Dashboard
- **URL:** `/dashboard/`
- **View Function:** `dashboard(request)`
- **Template:** `dashboard.html`
- **Workflow:** This is the primary hub after authentication. 
  - Retrieves all `UserProgress` records for the logged-in user.
  - Calculates percentage of completion, hours learned, and active courses.
  - Displays a dashboard view of all enrolled courses.

### 2.2 Course Creation (AI Builder)
- **URL:** `/course/create/`
- **View Function:** `course_input(request)`
- **Templates:** `course_form.html` (input) and `course_preview.html` (previewing outlined syllabus)
- **Workflow:**
  - **GET Request:** Shows a form (`course_form.html`) to configure course aspects (title, duration, hours per day, current level, required level, language).
  - **POST Request (Preview):** Uses the Groq LLM API via `gen_outline()` to generate a course outline. Renders `course_preview.html`.
  - **POST Request (Save):** Parses the generated outline into `Week` objects in the database, automatically enrolls the user via `UserProgress`, and redirects to the **Course Detail** page.

### 2.3 Course Catalog & Enrollment
- **URL:** `/courses/`
- **View Function:** `course_list(request)`
- **Template:** `course_list.html`
- **Description:** Displays all available courses in the database mapping.

- **URL:** `/course/<id>/enroll/`
- **View Function:** `enroll_course(request, course_id)`
- **Template:** None (Redirects to Dashboard)
- **Description:** Creates a `UserProgress` record for the user and the selected course, granting them access.

### 2.4 User Profile Management
- **URL:** `/profile/`
- **View Function:** `profile_view(request)`
- **Template:** `profile.html`
- **Description:** Allows the user to update their associated username and password.

---

## 3. Learning & Course Execution Workflow

### 3.1 Course Detail Overview
- **URL:** `/course/<id>/`
- **View Function:** `course_detail(request, course_id)`
- **Template:** `course_detail.html`
- **Workflow:**
  - Shows the complete list of weeks for the specific course.
  - Tracks total hours learned for the course and summarizes the AI-generated outline syllabus.

### 3.2 Weekly Lesson View
- **URL:** `/course/<id>/week/<number>/`
- **View Function:** `week_detail(request, course_id, week_number)`
- **Template:** `week_detail.html`
- **Workflow:**
  - The core learning interface. If daily content doesn't exist yet, it leverages the Groq LLM to dynamically generate comprehensive daily lesson contents (`Day` objects) based on the week's theme.
  - Generates YouTube video thumbnails and links relevant to the daily topic via the `search_youtube_video()` utility.
  - Displays the assignments and quizzes specific to that week.

### 3.3 Dynamic Quizzes
- **URL:** `/course/<id>/week/<number>/quiz/<id>/`
- **View Function:** `quiz_detail(request, course_id, week_number, quiz_id)`
- **Template:** `quiz_detail.html`
- **Workflow:**
  - Uses AI (`generate_quiz_content()`) to produce 5 multiple-choice questions based specifically on the week's generated content.
  - **POST Request:** Submits the quiz answers. Calculated via `calculate_quiz_score()` and redirected to the **Quiz Results** page.
- **Results URL:** `/course/.../quiz/<id>/result/`
- **Results Template:** `quiz_result.html`

### 3.4 Dynamic Assignments
- **URL:** `/course/<id>/week/<number>/assignment/<id>/`
- **View Function:** `assignment_detail(request, course_id, week_number, assignment_id)`
- **Template:** `assignment_detail.html`
- **Workflow:**
  - Dynamically uses AI (`generate_assignment_description()`) to create a practical exercise out of the week's topics.
  - Handles file uploads or text submissions for the assignment.

### 3.5 AI Chatbot Assistance
- **URLs:** `/chatbot/send/`, `/chatbot/conversation/`
- **View Functions:** `chatbot_send_message`, `chatbot_get_conversation`
- **Templates:** Processed via AJAX/JSON.
- **Workflow:** The user can interact with a course-specific AI tutor. The Groq LLM is prompted with context regarding the specific course Title to keep it focused on the course subject. It remembers previous messages in the session using the `ChatbotConversation` model.

### 3.6 Course Progress Tracking
- **URL:** `/update-progress/`
- **View Function:** `update_progress(request)`
- **Template:** Processed via AJAX/JSON.
- **Workflow:** As a user completes daily lessons, frontend JavaScript issues POST requests mapping the completed `Day` to their `UserProgress.completed_days` array.
