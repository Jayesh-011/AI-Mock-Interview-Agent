# 🚀 AI Mock Interview Agent

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)

![MongoDB](https://img.shields.io/badge/MongoDB-Database-green?style=for-the-badge&logo=mongodb)

![Ollama](https://img.shields.io/badge/Ollama-LLM-black?style=for-the-badge)

![AI](https://img.shields.io/badge/AI-Powered-orange?style=for-the-badge)

</p>

---

## 🎯 Overview

AI Mock Interview Agent is an intelligent interview preparation platform that:

✅ Collects interview questions from the web

✅ Stores them in MongoDB

✅ Conducts AI-powered mock interviews

✅ Evaluates candidate answers using LLMs

✅ Generates detailed interview reports

The project demonstrates practical implementation of:

- 🤖 AI Agents
- 🧠 Large Language Models
- 🔍 Retrieval-Augmented Generation (RAG)
- 📚 MongoDB Integration
- 🌐 Web Scraping
- 📊 Automated Evaluation Systems

---

## ✨ Features

### 🌐 Question Collection Engine

- Searches interview questions from the internet
- Extracts content using Trafilatura
- Uses LLM for question extraction
- Removes duplicate questions
- Stores structured data in MongoDB

---

### 🤖 AI Interview Agent

- Full Interview Mode
- Topic-wise Interview Mode
- Interactive Question & Answer Flow
- Intelligent Answer Evaluation

---

### 📈 Evaluation System

For every answer the agent provides:

- ✅ Score (0–10)
- ✅ Technical Evaluation
- ✅ Missing Concepts
- ✅ Improved Answer
- ✅ Interview Suggestions

---

### 📄 Report Generation

Generates detailed reports including:

- Candidate Information
- Question-wise Analysis
- Total Score
- Average Score
- Overall Performance

---

## 🏗️ Architecture

```text
Internet
    │
    ▼
fetch_questions.py
    │
    ▼
MongoDB
    │
    ▼
main.py
    │
    ▼
MockInterviewAgent
    │
    ▼
Ollama LLM
    │
    ▼
Interview Evaluation
    │
    ▼
Report Generator
```

---

## 📁 Project Structure

```text
project/

├── fetch_questions.py
├── interview_agent.py
├── llm_engine.py
├── main.py
├── report_generator.py
│
├── reports/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|----------|
| Python | Backend Development |
| MongoDB | Question Storage |
| Ollama | Local LLM Execution |
| Llama 3 | Answer Evaluation |
| Qwen 2.5 | Question Extraction |
| DDGS | Web Search |
| Trafilatura | Content Extraction |

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/AI-Mock-Interview-Agent.git

cd AI-Mock-Interview-Agent
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Start MongoDB

```bash
mongod
```

---

### 5️⃣ Start Ollama

```bash
ollama serve
```

Pull Model:

```bash
ollama pull llama3
```

or

```bash
ollama pull qwen2.5:3b
```

---

## 🚀 Usage

### Step 1 – Collect Questions

```bash
python fetch_questions.py
```

---

### Step 2 – Start Interview

```bash
python main.py
```

---

## 📊 Sample Workflow

```text
User
 │
 ▼
Answer Question
 │
 ▼
LLM Evaluation
 │
 ▼
Score Generation
 │
 ▼
Feedback
 │
 ▼
Final Report
```

---

## 🔮 Future Enhancements

- 🎙 Voice-based Interviews
- 📄 Resume Analysis
- 🌍 Multi-language Support
- 🖥 Streamlit Dashboard
- 📊 Candidate Analytics
- 📱 Web Application

---

## 👨‍💻 Author

### Jayesh Patil

AI | Machine Learning | Generative AI | Python

---

## ⭐ Support

If you found this project useful:

⭐ Star the repository

🍴 Fork the repository

🚀 Build something awesome with it

---

## 📜 License

This project is developed for educational and learning purposes.