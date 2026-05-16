import os

base = 'C:/disco J/SHOPSTARTER/shopstarter_back'
cleanup = [
    'check_syntax.py', 'check_indent.py', 'check_indent2.py',
    'check_all_syntax.py', 'check_schema.py', 'check_schema2.py',
    'check_filters.py', 'check_context.py', 'find_remaining.py',
    'find_end.py', 'find_end2.py', 'remove_dup.py', 'fix_schema.py',
    'fix_schema_run.py', 'fix_schema_v2.py', 'fix_schema_v3.py',
    'fix_schema_v4.py', 'fix_schema_final.py', 'fix_schema_final2.py',
    'fix_schema_clean.py', 'fix_indent.py', 'rebuild_schema.py',
    'generate_schema.py', 'rename_columns.py', 'validate.py',
    'verify.py', 'run_migration.ps1', 'gen_mig.ps1', 'gen_schema.ps1',
    'gen_schema3.ps1', 'gen_schema2.ps1',
    # Generated files
    'schema_new.yml',
]

for f in cleanup:
    path = os.path.join(base, f)
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed: {f}")

print("\nCleanup complete.")