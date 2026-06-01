import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json

def run():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get("http://localhost:8000/login")
        time.sleep(2)
        driver.find_element(By.NAME, "email").send_keys("admin@appverbo.local")
        driver.find_element(By.NAME, "password").send_keys("NovaSenhaForte123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)
        
        driver.get("http://localhost:8000/users/new?menu=meu_perfil")
        time.sleep(3)
        
        # Execute script to get sidebarMenuSettings for meu_perfil
        settings_js = driver.execute_script("""
            const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
            const settings = bootstrap.sidebarMenuSettings || [];
            const meu_perfil_setting = settings.find(s => s.key === 'meu_perfil');
            return meu_perfil_setting ? (meu_perfil_setting.process_subsequent_rules || meu_perfil_setting.process_subsequent_fields || meu_perfil_setting.process_subsequent || []) : null;
        """)
        
        print(json.dumps(settings_js, indent=2, ensure_ascii=False))
        
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
