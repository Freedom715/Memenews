from requests import get

print(get('http://localhost:5000/api/jobs').json())
print(get('http://localhost:5000/api/jobs/4').json())
print(get('http://localhost:5000/api/jobs/404').json())
print(get('http://localhost:5000/api/jobs/job_4').json())