import urllib.request

try:
    url = "http://localhost:8000/users/new?menu=sessoes&admin_tab=sessoes&sidebar_sections_tab=sessoes"
    response = urllib.request.urlopen(url, timeout=5)
    print(f"Status Code: {response.status}")
    html = response.read().decode("utf-8")
    print("Success! Page fetched.")
except Exception as e:
    print(f"Failed to fetch page: {e}")
