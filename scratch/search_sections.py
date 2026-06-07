import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def search_dict(d, path=""):
    results = []
    if isinstance(d, dict):
        for k, v in d.items():
            current_path = f"{path}.{k}" if path else k
            if any(x in str(k).lower() or x in str(v).lower() for x in ["dados gerais", "igreja", "sessoes", "sessões"]):
                results.append((current_path, v))
            results.extend(search_dict(v, current_path))
    elif isinstance(d, list):
        for idx, item in enumerate(d):
            current_path = f"{path}[{idx}]"
            results.extend(search_dict(item, current_path))
    return results

def main():
    with SessionLocal() as session:
        rows = session.execute(text("SELECT id, menu_key, menu_label, menu_config FROM sidebar_menu_settings")).all()
        for r in rows:
            if r.menu_config:
                try:
                    cfg = json.loads(r.menu_config)
                    matches = search_dict(cfg)
                    if matches:
                        print("="*80)
                        print(f"Menu Key: {r.menu_key} | Label: {r.menu_label}")
                        for path, val in matches:
                            # Print only a snippet if it's too long
                            val_str = str(val)
                            if len(val_str) > 100:
                                val_str = val_str[:100] + "..."
                            print(f"  Path: {path} -> {val_str}")
                except Exception as e:
                    print(f"Error parsing menu {r.menu_key}: {e}")

if __name__ == '__main__':
    main()
