import urllib.request

try:
    with urllib.request.urlopen('http://localhost:8000/') as response:
        html = response.read().decode('utf-8')
        
    has_toggle = 'id="themeToggle"' in html
    has_script = 'src="theme.js"' in html
    
    print(f"HAS_TOGGLE: {has_toggle}")
    print(f"HAS_SCRIPT: {has_script}")
    
except Exception as e:
    print(f"Error: {e}")
