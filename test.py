from requests import get
from help_functions import get_time

# print(get('http://localhost:5000/api/jobs').json())
# print(get('http://localhost:5000/api/jobs/4').json())
# print(get('http://localhost:5000/api/jobs/404').json())
# print(get('http://localhost:5000/api/jobs/job_4').json())
print(get_time("2019-03-30", "20:00"))
print(get_time("2019-03-29", "20:00"))
print(get_time("2019-03-28", "20:00"))