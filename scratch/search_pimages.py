import os

for root, dirs, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or 'venv' in root or '.venv' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.sql') or file.endswith('.yml'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if 'products_pimages' in content:
                    print(f"Found products_pimages in: {path}")
            except Exception as e:
                pass
