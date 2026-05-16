"""Fix corrupted schema.yml by rebuilding CrePro/PatchedCrePro/ReadPro sections."""
import re
import yaml

INPUT = 'C:/disco J/SHOPSTARTER/shopstarter_back/schema.yml'

# Read raw text
with open(INPUT, encoding='utf-8', errors='replace') as f:
    raw = f.read()

# Extract all lines for analysis
lines = raw.split('\n')

# Find the line numbers of the three schemas and their 'required:' sections
schema_markers = []
for i, line in enumerate(lines):
    stripped = line.lstrip()
    if stripped in ('CrePro:', 'PatchedCrePro:', 'ReadPro:'):
        schema_markers.append((i, stripped[:-1]))  # (line_num, schema_name)

print("Schema markers found:", schema_markers)

# For each schema, find its 'required:' line (at same indent as the schema itself)
def find_required_after(start_line, lines, base_indent):
    """Find the 'required:' line that matches the base_indent."""
    for i in range(start_line, min(start_line + 200, len(lines))):
        stripped = lines[i].strip()
        line_indent = len(lines[i]) - len(lines[i].lstrip())
        if stripped.startswith('required:') and line_indent == base_indent:
            return i
        # If we hit another top-level schema, stop
        if stripped in ('CrePro:', 'PatchedCrePro:', 'ReadPro:', 'Register:',
                        'PatchedCategory:', 'PatchedLocation:', 'Problem:',
                        'PaginatedReadPro:', 'PaginatedCategory:',
                        'PaginatedProduct:', 'PaginatedOrder:',
                        'PaginatedReview:', 'PaginatedImage:',
                        'PaginatedVendor:', 'PaginatedAudit:',
                        'PaginatedCoupon:', 'PaginatedMessage:',
                        'PaginatedCategoryProduct:',
                        'Status308Enum:', 'RoleEnum:'):
            if i > start_line + 2:
                return -1
    return -1

def extract_field_name(line):
    """Extract property name from a YAML line."""
    stripped = line.strip()
    if ':' in stripped and not stripped.startswith(('type:', 'format:', 'readOnly:',
                                                     'nullable:', 'maxLength:',
                                                     'pattern:', 'minimum:',
                                                     'maximum:', 'items:',
                                                     '$ref:', 'description:',
                                                     'example:', 'title:',
                                                     'default:', 'enum:',
                                                     'required:')):
        return stripped.split(':')[0]
    return None

# Now rebuild each schema's properties section
for schema_idx, (start_line, schema_name) in enumerate(schema_markers):
    print(f"\nProcessing {schema_name}...")

    # Determine base indent
    base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
    print(f"  Base indent: {base_indent}")

    # Skip to 'properties:'
    props_line = None
    for i in range(start_line, min(start_line + 200, len(lines))):
        stripped = lines[i].strip()
        if stripped == 'properties:':
            indent = len(lines[i]) - len(lines[i].lstrip())
            if indent == base_indent + 8:
                props_line = i
                print(f"  Properties at line {i+1}")
                break

    if props_line is None:
        print(f"  SKIP: No properties line found")
        continue

    # Find required: line
    req_line = find_required_after(props_line, lines, base_indent + 6)
    if req_line == -1:
        print(f"  SKIP: No required line found")
        continue

    print(f"  Required at line {req_line + 1}")

    # Collect existing field definitions between properties: and required:
    field_names = []
    for i in range(props_line + 1, req_line):
        fname = extract_field_name(lines[i])
        if fname and fname not in ('type', 'format', 'readOnly', 'nullable', 'maxLength',
                                     'pattern', 'minimum', 'maximum', 'items', '$ref',
                                     'description', 'example', 'title', 'default', 'enum'):
            # Avoid duplicates
            if not field_names or field_names[-1] != fname:
                field_names.append(fname)

    print(f"  Fields found: {field_names}")

print("\n\nDone analyzing. Now need to rebuild the schema properly.")
print("The fastest approach: rebuild the schema.yml from scratch using a known-good template.")