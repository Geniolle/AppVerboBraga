import urllib.request
import urllib.parse
import http.cookiejar
import re
import json

def test_login_and_get_page():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # 1. Login
    login_url = "http://localhost:8000/login"
    login_data = urllib.parse.urlencode({
        "email": "verbodavidabraga@gmail.com",
        "password": "TesteApp123!",
        "login_mode": "login"
    }).encode("utf-8")
    opener.open(urllib.request.Request(login_url, data=login_data, method="POST"))

    # 2. Get page
    url = "http://localhost:8000/users/new?menu=contacto_geral"
    with opener.open(urllib.request.Request(url)) as resp:
        html = resp.read().decode("utf-8")
        
        # Extract bootstrap
        bootstrap_match = re.search(r'window\.__APPVERBO_BOOTSTRAP__\s*=\s*(\{.*?\});', html, re.DOTALL)
        if bootstrap_match:
            bootstrap_str = bootstrap_match.group(1)
            for line in bootstrap_str.splitlines():
                if "menuProcessValuesMap:" in line:
                    json_str = line.strip().replace("menuProcessValuesMap: ", "").rstrip(",")
                    values_map = json.loads(json_str)
                    print("menuProcessValuesMap for contacto_geral:")
                    print(json.dumps(values_map.get("contacto_geral"), indent=2))
                    return
        else:
            print("Bootstrap not found in HTML!")

if __name__ == "__main__":
    test_login_and_get_page()
