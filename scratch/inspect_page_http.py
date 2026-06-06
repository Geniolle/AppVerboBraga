import urllib.request
import urllib.parse
import http.cookiejar

def test_get_js_file():
    # Fetch from server
    url = "http://localhost:8000/static/js/modules/dynamic_process_runtime_core_v1.js?v=20260606-dynamic-runtime-core-v13-n-cliente"
    print(f"Fetching {url}...")
    try:
        with urllib.request.urlopen(url) as resp:
            print("Response status:", resp.status)
            content = resp.read().decode("utf-8")
            print("Checking content for 'custom_n_cliente':")
            lines = content.splitlines()
            found = False
            for idx, line in enumerate(lines):
                if "custom_n_cliente" in line:
                    print(f"Line {idx+1}: {line.strip()}")
                    found = True
            if not found:
                print("NOT FOUND!")
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.reason)

if __name__ == "__main__":
    test_get_js_file()
