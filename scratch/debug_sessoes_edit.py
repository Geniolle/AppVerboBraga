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
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)
        
        # Check if login succeeded
        print("Current URL after login:", driver.current_url)
        
        # 3. Go to sessoes page directly
        print("Going to Sessões...")
        driver.get("http://localhost:8000/users/new?menu=sessoes&admin_tab=sessoes&sidebar_sections_tab=sessoes")
        time.sleep(3)
        print("URL after navigation:", driver.current_url)
        
        # 4. Find all edit links
        edit_links = driver.find_elements(By.CSS_SELECTOR, "a[title='Editar']")
        print(f"Found {len(edit_links)} Edit buttons.")
        for idx, link in enumerate(edit_links):
            href = link.get_attribute("href")
            print(f"Edit Link {idx}: href='{href}'")
            
        if edit_links:
            # Click the first edit link
            print("Clicking first Edit link...")
            first_link = edit_links[0]
            # Print parent row details
            row = first_link.find_element(By.XPATH, "./ancestor::tr")
            print("Row text:", row.text.encode('utf-8'))
            
            first_link.click()
            time.sleep(3)
            print("URL after clicking Edit:", driver.current_url)
            
            # Print browser console logs
            print("\n--- BROWSER CONSOLE LOGS ---")
            logs = driver.get_log('browser')
            for log in logs:
                print(f"[{log['level']}] {log['message']}")
                
            # Check if edit card exists and is visible
            print("\n--- Edit Card Check ---")
            edit_cards = driver.find_elements(By.CSS_SELECTOR, "#admin-sidebar-sections-form-card")
            print(f"Found {len(edit_cards)} cards matching #admin-sidebar-sections-form-card")
            for idx, card in enumerate(edit_cards):
                print(f"Card {idx}: visible={card.is_displayed()}")
                print(f"Card {idx} classes={card.get_attribute('class')} style='{card.get_attribute('style')}'")
                # print first 300 chars of HTML
                print(f"Card {idx} HTML snippet: {card.get_attribute('outerHTML')[:400]}")
                
            # Check active/inactive cards too
            active_cards = driver.find_elements(By.CSS_SELECTOR, "#admin-sidebar-sections-card")
            print(f"Found {len(active_cards)} cards matching #admin-sidebar-sections-card")
            for idx, card in enumerate(active_cards):
                print(f"Active Card {idx}: visible={card.is_displayed()}")
                
            inactive_cards = driver.find_elements(By.CSS_SELECTOR, "#admin-sidebar-sections-card-inactive")
            print(f"Found {len(inactive_cards)} cards matching #admin-sidebar-sections-card-inactive")
            for idx, card in enumerate(inactive_cards):
                print(f"Inactive Card {idx}: visible={card.is_displayed()}")
        else:
            print("No edit links found to click.")
            
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
