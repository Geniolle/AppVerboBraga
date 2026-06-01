import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def run():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    try:
        # 1. Open login page
        print("Opening login page...")
        driver.get("http://localhost:8000/login")
        time.sleep(2)
        
        # 2. Fill login form
        print("Logging in...")
        driver.find_element(By.NAME, "email").send_keys("admin@appverbo.local")
        driver.find_element(By.NAME, "password").send_keys("NovaSenhaForte123")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)
        
        # Check if login succeeded (URL should change)
        print("Current URL after login:", driver.current_url)
        
        # 3. Go to Meu perfil page directly
        print("Going to Meu Perfil...")
        driver.get("http://localhost:8000/users/new?menu=meu_perfil")
        time.sleep(3)
        
        # 4. Click the tab "Dados de agregados"
        print("Clicking 'Dados de agregados'...")
        # Let's find the tab button
        tabs = driver.find_elements(By.CSS_SELECTOR, ".menu-tabs a, .menu-tabs button, .submenu-item")
        for tab in tabs:
            text = tab.text.lower()
            if "agregados" in text:
                print("Found tab:", tab.text)
                tab.click()
                break
        time.sleep(2)
        
        # Print browser console logs
        print("\n--- BROWSER CONSOLE LOGS ---")
        logs = driver.get_log('browser')
        for log in logs:
            print(f"[{log['level']}] {log['message']}")
            
        # Inspect element visibility of custom_nome_do_conjuge in view mode
        conjuge_wrapper = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card [data-profile-field-key='custom_nome_do_conjuge']")
        print("\nconjuge wrapper visible?", conjuge_wrapper.is_displayed())
        print("conjuge wrapper class/style:", conjuge_wrapper.get_attribute("class"), "/", conjuge_wrapper.get_attribute("style"))
        
        # Check trigger field custom_estado_civil value
        estado_civil_wrapper = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card [data-profile-field-key='custom_estado_civil']")
        print("estado_civil wrapper visible?", estado_civil_wrapper.is_displayed())
        print("estado_civil wrapper innerHTML:", estado_civil_wrapper.get_attribute("innerHTML"))
        print("estado_civil data-profile-section-pane:", estado_civil_wrapper.get_attribute("data-profile-section-pane"))
        print("estado_civil dataset:", driver.execute_script("return document.querySelector(\"#perfil-pessoal-card [data-profile-field-key='custom_estado_civil']\").dataset;"))
        
        conjuge_wrapper = driver.find_element(By.CSS_SELECTOR, "#perfil-pessoal-card [data-profile-field-key='custom_nome_do_conjuge']")
        print("conjuge data-profile-section-pane:", conjuge_wrapper.get_attribute("data-profile-section-pane"))
        print("conjuge dataset:", driver.execute_script("return document.querySelector(\"#perfil-pessoal-card [data-profile-field-key='custom_nome_do_conjuge']\").dataset;"))
        
        # Test the selector logic
        readonly_text = driver.execute_script("""
            const wrapper = document.querySelector("#perfil-pessoal-card [data-profile-field-key='custom_estado_civil']");
            if (!wrapper) return "no wrapper";
            const valueElement = wrapper.querySelector(".personal-value, strong, output");
            if (valueElement) return "valueElement: " + valueElement.textContent.trim();
            const labelElement = wrapper.querySelector(".personal-label, label");
            const labelText = labelElement ? labelElement.textContent.trim() : "";
            const fullText = wrapper.textContent.trim();
            return "fullText: " + fullText + " | labelText: " + labelText;
        """)
        print("Readonly JS execution results:", readonly_text)

        # Inspect tab elements
        print("\n--- Tabs Info ---")
        tabs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Dados de agregados')]")
        for tab in tabs:
            print("Tag:", tab.tag_name)
            print("Text:", tab.text)
            print("Class:", tab.get_attribute("class"))
            print("Dataset:", driver.execute_script("return arguments[0].dataset;", tab))
            print("Parent Tag/Class:", tab.find_element(By.XPATH, "..").tag_name, "/", tab.find_element(By.XPATH, "..").get_attribute("class"))
            print("Parent InnerHTML:", tab.find_element(By.XPATH, "..").get_attribute("innerHTML")[:300])
        
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
