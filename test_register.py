import requests

url = "http://127.0.0.1:5000/register"
files = {'file': open("p1.jpg", 'rb')}
data = {'username': 'test_user'}

response = requests.post(url, files=files, data=data)
print("Response Status Code:", response.status_code)
print("Response Text:", response.text)
