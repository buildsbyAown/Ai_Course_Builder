# Course Builder Backend (FYP)

 This is the backend for the Course Builder application, built with Django. It handles course management, user progress tracking, quizzes, and assignments.

 ## Features

 - **Course Management**: Create and manage courses with detailed outlines (weeks/days).
 - **User Progress**: Track user enrollment and completion of course materials.
 - **Quizzes**: Support for weekly quizzes with scoring.
 - **Assignments**: Assignment submission and grading functionality.
 - **AI Integration**: Uses Groq API for content generation (implied by requirements).

 ## Project Structure

 - `coursebuilder/`: Main application containing models for Courses, Weeks, Days, Quizzes, Assignments, and User Progress.
 - `fyp/`: Project configuration settings.
 - `templates/`: HTML templates for the backend views.

 ## Prerequisites

 - Python 3.8+
 - `pip` (Python package installer)

 ## Setup

 1. **Navigate to the project directory:**
    ```bash
    cd fyp
    ```

 2. **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

 3. **Install dependencies:**
    The requirements file is located in the parent directory.
    ```bash
    pip install -r ../requirements.txt
    ```

 4. **Apply migrations:**
    Initialize the database schema.
    ```bash
    python manage.py migrate
    ```

 5. **Create a superuser (for admin access):**
    ```bash
    python manage.py createsuperuser
    ```

 ## Running the Server

 Start the development server:

 ```bash
 python manage.py runserver
 ```

 The application will be available at `http://127.0.0.1:8000/`.

 ## Environment Variables

 Make sure to set up your `.env` file in the `fyp` directory if required (referenced in root files).
