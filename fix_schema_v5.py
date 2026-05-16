"""Fix schema.yml by rebuilding exact property blocks for the 3 product schemas."""
import re

INPUT = 'C:/disco J/SHOPSTARTER/shopstarter_back/schema.yml'

with open(INPUT, encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find the exact line ranges for the three schemas' properties blocks
# CrePro: schema at some line, properties at line 3079 (indent 8), required somewhere
# PatchedCrePro: schema at some line, properties at line 3464 (indent 7)
# ReadPro: schema at some line, properties at line 3619 (indent 8)

# Step 1: Find properties: and required: lines for each
def find_props_and_req(lines, schema_line):
    """Find properties: and required: lines for a schema starting at schema_line."""
    props = None
    req = None
    for i in range(schema_line, min(schema_line + 100, len(lines))):
        stripped = lines[i].strip()
        if stripped == 'properties:' and props is None:
            props = i
        if stripped.startswith('required:') and props is not None:
            # Check this is at the right level (same indent as properties or higher)
            if req is None:
                req = i
                break
    return props, req

# Find schema lines
schema_lines = {}
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped in ('CrePro:', 'PatchedCrePro:', 'ReadPro:'):
        schema_lines[stripped[:-1]] = i

print("Schema lines:", schema_lines)

for name in ('CrePro', 'PatchedCrePro', 'ReadPro'):
    sline = schema_lines[name]
    props_line, req_line = find_props_and_req(lines, sline)
    print(f"{name}: schema={sline+1}, properties={props_line+1 if props_line else None}, required={req_line+1 if req_line else None}")

    if props_line is None or req_line is None:
        print(f"  SKIPPING {name}")
        continue

    # Determine indent of schema line
    schema_indent = len(lines[sline]) - len(lines[sline].lstrip())

    # Build property block with correct indentation
    # Properties should be at schema_indent + 1 (or similar)
    p_indent = len(lines[props_line]) - len(lines[props_line].lstrip())
    s_indent = p_indent + 2
    ss_indent = s_indent + 2

    def pin(s=''):
        return ' ' * p_indent + s

    def sin(s=''):
        return ' ' * s_indent + s

    def ssin(s=''):
        return ' ' * ss_indent + s

    new_props = []

    if name == 'CrePro':
        new_props = [
            pin('id:'),
            sin('type: string'),
            sin('format: uuid'),
            sin('readOnly: true'),
            pin('vendor:'),
            sin('type: string'),
            sin('format: uuid'),
            sin('readOnly: true'),
            pin('categories:'),
            sin('type: array'),
            sin('items:'),
            ssin('type: integer'),
            sin('readOnly: true'),
            pin('category_names:'),
            sin('type: array'),
            sin('items:'),
            ssin('type: string'),
            sin('readOnly: true'),
            pin('name:'),
            sin('type: string'),
            sin('maxLength: 255'),
            pin('description:'),
            sin('type: string'),
            pin('ai_description:'),
            sin('type: string'),
            sin('nullable: true'),
            pin('price:'),
            sin('type: string'),
            sin('format: decimal'),
            sin('pattern: ^-?\\d{0,8}(?:\\.\\d{0,2})?$'),
            pin('stock:'),
            sin('type: integer'),
            sin('maximum: 9223372036854775807'),
            sin('minimum: 0'),
            sin('format: int64'),
            pin('status:'),
            sin('$ref: ' + "'#/components/schemas/Status308Enum'"),
            pin('rejection_reason:'),
            sin('type: string'),
            sin('nullable: true'),
            pin('is_featured:'),
            sin('type: boolean'),
            pin('images:'),
            sin('type: array'),
            sin('items:'),
            ssin("$ref: '#/components/schemas/PImageWrite'"),
            sin('readOnly: true'),
            pin('is_deleted:'),
            sin('type: boolean'),
        ]
    elif name == 'PatchedCrePro':
        new_props = [
            pin('id:'),
            sin('type: string'),
            sin('format: uuid'),
            sin('readOnly: true'),
            pin('vendor:'),
            sin('type: string'),
            sin('format: uuid'),
            sin('readOnly: true'),
            pin('categories:'),
            sin('type: array'),
            sin('items:'),
            ssin('type: integer'),
            sin('readOnly: true'),
            pin('category_names:'),
            sin('type: array'),
            sin('items:'),
            ssin('type: string'),
            sin('readOnly: true'),
            pin('name:'),
            sin('type: string'),
            sin('maxLength: 255'),
            pin('description:'),
            sin('type: string'),
            pin('ai_description:'),
            sin('type: string'),
            sin('nullable: true'),
            pin('price:'),
            sin('type: string'),
            sin('format: decimal'),
            sin('pattern: ^-?\\d{0,8}(?:\\.\\d{0,2})?$'),
            pin('stock:'),
            sin('type: integer'),
            sin('maximum: 9223372036854775807'),
            sin('minimum: 0'),
            sin('format: int64'),
            pin('status:'),
            sin('$ref: ' + "'#/components/schemas/Status308Enum'"),
            pin('rejection_reason:'),
            sin('type: string'),
            sin('nullable: true'),
            pin('is_featured:'),
            sin('type: boolean'),
            pin('images:'),
            sin('type: array'),
            sin('items:'),
            ssin("$ref: '#/components/schemas/PImageWrite'"),
            sin('readOnly: true'),
            pin('is_deleted:'),
            sin('type: boolean'),
        ]
    elif name == 'ReadPro':
        new_props = [
            pin('id:'),
            sin('type: string'),
            sin('format: uuid'),
            sin('readOnly: true'),
            pin('vendor:'),
            sin('type: string'),
            sin('format: uuid'),
            pin('vendor_name:'),
            sin('type: string'),
            sin('readOnly: true'),
            pin('categories:'),
            sin('type: array'),
            sin('items:'),
            ssin("$ref: '#/components/schemas/Category'"),
            sin('readOnly: true'),
            pin('category_names:'),
            sin('type: array'),
            sin('items:'),
            ssin('type: string'),
            sin('readOnly: true'),
            pin('name:'),
            sin('type: string'),
            sin('maxLength: 255'),
            pin('description:'),
            sin('type: string'),
            pin('ai_description:'),
            sin('type: string'),
            sin('nullable: true'),
            pin('price:'),
            sin('type: string'),
            sin('format: decimal'),
            sin('pattern: ^-?\\d{0,8}(?:\\.\\d{0,2})?$'),
            pin('stock:'),
            sin('type: integer'),
            sin('maximum: 9223372036854775807'),
            sin('minimum: 0'),
            sin('format: int64'),
            pin('status:'),
            sin('$ref: ' + "'#/components/schemas/Status308Enum'"),
            pin('rejection_reason:'),
            sin('type: string'),
            sin('nullable: true'),
            pin('is_featured:'),
            sin('type: boolean'),
            pin('images:'),
            sin('type: array'),
            sin('items:'),
            ssin("$ref: '#/components/schemas/PImageRead'"),
            sin('readOnly: true'),
            pin('created_at:'),
            sin('type: string'),
            sin('format: date-time'),
            sin('readOnly: true'),
            pin('distance:'),
            sin('type: string'),
            sin('readOnly: true'),
            pin('latitude:'),
            sin('type: string'),
            sin('readOnly: true'),
            pin('longitude:'),
            sin('type: string'),
            sin('readOnly: true'),
            pin('is_deleted:'),
            sin('type: boolean'),
        ]
    else:
        continue

    # Add empty line before required
    new_props.append('')

    # Find the required line
    req_line_text = lines[req_line]

    # Replace lines[props_line+1 : req_line] with new_props
    # Also include props_line itself (we keep properties: line)
    replacement = [l + '\n' for l in new_props]
    new_lines = lines[:props_line+1] + replacement + lines[req_line:]
    lines = new_lines

    # Update schema line positions for subsequent schemas
    old_count = req_line - props_line - 1
    new_count = len(new_props)
    delta = new_count - old_count
    for n in schema_lines:
        if schema_lines[n] > req_line:
            schema_lines[n] += delta

    print(f"  Replaced {old_count} lines with {new_count} lines (delta={delta})")

# Write
with open(INPUT, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\nWrote {INPUT}, {len(lines)} lines")

# Validate
import yaml
with open(INPUT, encoding='utf-8') as f:
    data = yaml.safe_load(f)
print("\nYAML VALID!")
for name in ('CrePro', 'PatchedCrePro', 'ReadPro'):
    s = data['components']['schemas'].get(name, {})
    p = s.get('properties', {})
    cats = [k for k in p if 'categor' in k]
    print(f"  {name}: {cats}")