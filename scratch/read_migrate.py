with open('migrate_output.txt', 'r', encoding='utf-16') as f:
    content = f.read()
print(content[:2000].encode('utf-8', errors='ignore').decode('cp1252', errors='ignore'))
