import asyncio
from fastapi import Request
from appverbo.routes.profile.page_handler import new_user_page

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
        "query_string": b"menu=sessoes&admin_tab=menu&target=settings-menu-edit-card&settings_edit_key=sessoes&settings_action=edit",
    }
    req = MockRequest(scope)
    
    response = new_user_page(
        request=req,
        menu="sessoes",
        admin_tab="menu",
        settings_edit_key="sessoes",
        settings_action="edit",
        target="settings-menu-edit-card"
    )
    
    html_content = response.body.decode('utf-8')
    
    print("--- SEARCHING FOR EDIT CARD (settings_edit_key=sessoes) ---")
    pos = html_content.find('id="settings-menu-edit-card"')
    if pos != -1:
        print("settings-menu-edit-card found at index", pos)
        snippet = html_content[pos-50 : pos+300]
        print("Snippet:")
        print(snippet)
    else:
        print("settings-menu-edit-card NOT found")

if __name__ == '__main__':
    asyncio.run(main())
