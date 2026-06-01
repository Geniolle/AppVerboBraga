from fastapi import Request
from appverbo.routes.profile.page_handler import new_user_page
import re
import asyncio

# Mock Request class
class MockRequest(Request):
    def __init__(self, scope, receive=None, send=None):
        super().__init__(scope, receive, send)
        self._session = {"user_id": 1, "entity_id": 1, "user_name": "Admin Sistema", "user_email": "admin@appverbo.local"}

    @property
    def session(self):
        return self._session

async def main():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users/new",
        "headers": [],
        "query_string": b"menu=meu_perfil&profile_section=custom_dados_de_agregados",
    }
    req = MockRequest(scope)
    
    response = new_user_page(
        request=req,
        menu="meu_perfil",
        profile_section="custom_dados_de_agregados"
    )
    
    html_content = response.body.decode('utf-8')
    
    print("--- CARD PRESENCE ---")
    if "perfil-pessoal-card" in html_content:
        print("#perfil-pessoal-card is present!")
    else:
        print("#perfil-pessoal-card is NOT present!")
        
    print("\n--- OCCURRENCES OF custom_estado_civil ---")
    # find divs containing custom_estado_civil
    pattern = re.compile(r'<div[^>]*data-profile-field-key="custom_estado_civil"[^>]*>.*?</div>', re.DOTALL)
    matches = pattern.findall(html_content)
    for i, match in enumerate(matches, 1):
        print(f"Match {i}:")
        print(match)
        
    print("\n--- OCCURRENCES OF custom_nome_do_conjuge ---")
    pattern = re.compile(r'<div[^>]*data-profile-field-key="custom_nome_do_conjuge"[^>]*>.*?</div>', re.DOTALL)
    matches = pattern.findall(html_content)
    for i, match in enumerate(matches, 1):
        print(f"Match {i}:")
        print(match)

if __name__ == '__main__':
    asyncio.run(main())
