import requests

url = "http://127.0.0.1:5000/verify"
files = {'file': open("p1.jpg", 'rb')}

response = requests.post(url, files=files)
print("Response Status Code:", response.status_code)
print("Response Text:", response.text)
