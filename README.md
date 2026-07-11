# 🎓 AI Course Builder

An AI-powered platform that automatically generates structured, personalized courses from any topic using Large Language Models (LLMs). The system creates complete learning paths, modules, lessons, quizzes, and learning objectives, enabling educators and learners to build high-quality courses in minutes instead of days.

---

## 🚀 Features

- 🤖 AI-generated course outlines
- 📚 Automatic module and lesson generation
- 🎯 Learning objectives for every module
- ❓ AI-generated quizzes and assessments
- 📖 Lesson summaries and explanations
- 🔄 Course regeneration and refinement
- 💾 Save and manage generated courses
- 🌐 REST API for seamless frontend integration
- ⚡ Fast and scalable architecture

---

## 🏗️ Architecture

```
                +----------------+
                |   Frontend     |
                | (React/Next.js)|
                +-------+--------+
                        |
                    REST API
                        |
                +-------v--------+
                |   Backend API  |
                | (FastAPI)      |
                +-------+--------+
                        |
        +---------------+----------------+
        |                                |
+-------v--------+              +--------v-------+
|  AI Service    |              |   Database     |
| OpenAI / LLM   |              | PostgreSQL     |
+----------------+              +----------------+
```

---

## 📂 Project Structure

```
AI-Course-Builder/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── database/
│   ├── prompts/
│   └── main.py
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── utils/
│
├── docs/
├── tests/
├── requirements.txt
├── package.json
└── README.md
```

---

## ⚙️ Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

### AI

- OpenAI GPT Models
- Prompt Engineering
- Structured JSON Outputs

### Frontend

- React / Next.js
- Tailwind CSS
- Axios

### DevOps

- Docker
- GitHub Actions
- Nginx

---

## 📦 Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/ai-course-builder.git

cd ai-course-builder
```

### Backend

```bash
python -m venv venv

source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env`

```env
OPENAI_API_KEY=your_api_key
DATABASE_URL=postgresql://user:password@localhost/coursebuilder
```

Run the backend

```bash
uvicorn main:app --reload
```

---

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## 💡 Usage

1. Enter a course topic.
2. Specify the difficulty level.
3. Choose the target audience.
4. Generate the course.
5. Review the AI-generated curriculum.
6. Edit or regenerate any module.
7. Export or publish the course.

---

## 📄 Example Prompt

```
Topic:
Machine Learning

Audience:
Beginners

Duration:
8 Weeks

Output:
- Course Overview
- Learning Objectives
- Weekly Modules
- Lessons
- Practical Exercises
- Final Project
- Quiz Questions
```

---

## 🔌 API Endpoints

### Generate Course

```
POST /api/course/generate
```

Example Request

```json
{
  "topic": "Machine Learning",
  "difficulty": "Beginner",
  "duration": "8 Weeks",
  "audience": "Students"
}
```

---

### Get Course

```
GET /api/course/{course_id}
```

---

### Update Course

```
PUT /api/course/{course_id}
```

---

### Delete Course

```
DELETE /api/course/{course_id}
```

---

## 🧠 AI Workflow

```
User Input
      │
      ▼
Prompt Builder
      │
      ▼
LLM
      │
      ▼
Structured JSON Output
      │
      ▼
Validation
      │
      ▼
Database
      │
      ▼
Frontend Rendering
```

---

## 📈 Future Improvements

- Multi-language course generation
- PDF and PowerPoint export
- Video lesson generation
- AI tutor/chat assistant
- Course marketplace
- Student progress tracking
- LMS integration (Moodle, Canvas)
- Adaptive learning paths

---

## 🧪 Testing

Backend

```bash
pytest
```

Frontend

```bash
npm test
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

---

## 📜 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

Developed as an AI-powered educational platform to automate curriculum creation and enhance personalized learning experiences.
