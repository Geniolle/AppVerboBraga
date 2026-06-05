import urllib.request
import re

url = "http://127.0.0.1:8000/users/new?menu=sessoes"
response = urllib.request.urlopen(url)
html = response.read().decode("utf-8")

match = re.search(r'<section id="menu-tabs-card".*?</section>', html, re.DOTALL)
if match:
    print(match.group(0))
else:
    print("menu-tabs-card not found.")
