# Skill-Match
The Skill Matching Portal is a web-based platform designed to bridge the gap between students and employers. Employers can post job requirements, while students can showcase their skills. The system uses cosine similarity to intelligently match student skill profiles with job descriptions, helping both parties find the best fit efficiently.
🚀 Key Features
👨‍🎓 Student Portal

Create and manage student profiles

Add and update technical & non-technical skills

View job postings

Check similarity score between skills and job requirements

🧑‍💼 Employer Portal

Employer registration and login

Post job roles with required skills

View matched student profiles based on similarity score

🤖 AI-Based Skill Matching

Text preprocessing (tokenization, vectorization)

Cosine similarity to measure skill-job relevance

Ranks students/jobs based on similarity percentage

🛠️ Technologies Used

Frontend: HTML, CSS

Backend: Python (Flask)

Machine Learning: TF-IDF / Bag of Words, Cosine Similarity

Database: SQLite / MySQL

Authentication: Session-based login

🧠 How Skill Matching Works

Students add their skills as text input

Employers post job descriptions with required skills

Text data is vectorized using TF-IDF

Cosine similarity is computed between skill sets and job requirements

Results are ranked and displayed as a similarity score
