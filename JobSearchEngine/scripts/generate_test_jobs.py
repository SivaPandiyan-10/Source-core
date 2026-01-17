#!/usr/bin/env python3
"""
Test data generator for JobSearchEngine.
Generates mock job listings for testing and demonstration.
"""

import json
import random
from datetime import datetime, timedelta

# Job data templates
COMPANIES = [
    "TechCorp", "DataSystems", "InnovateTech", "CloudService",
    "DataWorks", "Microservices", "SystemsCore", "PerformanceGain",
    "InfoSolutions", "CloudFirst", "NetConnect", "SecureNet"
]

ROLES = [
    "Senior Software Engineer", "Software Architect", "Principal Engineer",
    "Backend Engineering Lead", "Staff Software Engineer", "Go/C++ Developer",
    "Senior Backend Engineer", "Technical Lead", "Engineering Manager"
]

LOCATIONS = [
    "San Francisco", "Bay Area", "Remote", "New York", "Austin",
    "Seattle", "Los Angeles", "Bangalore", "London", "Toronto"
]

SKILLS = [
    "C++", "Go", "Python", "Java", "JavaScript", "TypeScript",
    "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "AWS", "Azure",
    "System Design", "Microservices", "React", "Node.js"
]

def generate_job_listing(job_id):
    """Generate a realistic job listing."""
    company = random.choice(COMPANIES)
    role = random.choice(ROLES)
    location = random.choice(LOCATIONS)
    skills = random.sample(SKILLS, random.randint(3, 6))
    exp_years = random.randint(2, 12)
    
    descriptions = [
        f"We are looking for a talented {role} to join our growing team.",
        f"Seeking experienced {role} with expertise in {', '.join(skills[:2])}.",
        f"{company} is hiring a {role} for our {location} office.",
    ]
    
    days_ago = random.randint(1, 60)
    posted_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
    
    return {
        "id": f"job_{job_id}",
        "title": role,
        "company": company,
        "location": location,
        "description": random.choice(descriptions),
        "apply_link": f"https://example.com/jobs/{job_id}",
        "source": random.choice(["LinkedIn", "Naukri"]),
        "posted_date": posted_date,
        "experience_required_years": exp_years,
        "required_skills": skills
    }

def generate_test_jobs(count=50):
    """Generate test job listings."""
    jobs = []
    for i in range(count):
        jobs.append(generate_job_listing(i + 1000))
    return jobs

def save_to_json(jobs, filename="test_jobs.json"):
    """Save job listings to JSON file."""
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"✓ Generated {len(jobs)} test jobs: {filename}")

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    output_file = sys.argv[2] if len(sys.argv) > 2 else "test_jobs.json"
    
    jobs = generate_test_jobs(count)
    save_to_json(jobs, output_file)
