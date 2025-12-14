from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match_student_to_job(student_skills, job_skills):
    # Convert to lowercase
    student_skills = student_skills.lower()
    job_skills = job_skills.lower()

    # Vectorize
    vectorizer = CountVectorizer().fit([student_skills, job_skills])
    vectors = vectorizer.transform([student_skills, job_skills])

    # Compute similarity
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    # Find missing skills
    student_set = set(student_skills.split(","))
    job_set = set(job_skills.split(","))
    missing_skills = list(job_set - student_set)

    return round(similarity, 2), missing_skills
