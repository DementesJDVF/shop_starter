"""Completely rebuild schema.yml by reassembling clean parts with corrected schemas."""
INPUT = 'C:/disco J/SHOPSTARTER/shopstarter_back/schema.yml'

# Since incremental edits have corrupted the file beyond repair,
# let me reconstruct it from scratch using the original template structure.
# I'll copy the good parts (header, paths, security, etc.) and rebuild schemas.

# First, let me get the clean pre-schemas section
with open(INPUT, encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Extract everything before schemas section (up to and including "components:")
pre_schemas = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == 'components:':
        pre_schemas.append(line)
        break
    pre_schemas.append(line)

print(f"Pre-schemas: {len(pre_schemas)} lines (up to line {len(pre_schemas)})")

# Extract everything after schemas section
# Find where schemas end (look for the last top-level key like "tags:" or end)
after_schemas = []
in_schemas = False
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == 'schemas:':
        in_schemas = True
    elif in_schemas:
        indent = len(line) - len(line.lstrip())
        # Top-level keys after schemas section have indent 0
        if stripped and indent == 0 and ':' in stripped and not stripped.startswith('#') and not stripped.startswith('-'):
            after_schemas = lines[i:]
            break

print(f"After-schemas: {len(after_schemas)} lines")

# Rebuild all schemas correctly
# Get the full list of schemas from the original
schemas_section = [
    # ActionTypeEnum - copied exactly
    ('ActionTypeEnum', """    ActionTypeEnum:
      enum:
      - CREATE
      - UPDATE
      - DELETE
      - SOFT_DELETE
      - RESTORE
      - STATUS_CHANGE
      - ROLE_CHANGE
      - LOGIN
      - LOGOUT
      - REFRESH
      - UNKNOWN"""),

    # CouponTypeEnum
    ('CouponTypeEnum', """    CouponTypeEnum:
      enum:
      - PERCENTAGE
      - FIXED_AMOUNT
      - BUY_ONE_GET_ONE
      - FREE_SHIPPING
      - FLASH_SALE"""),

    # CouponStatusEnum
    ('CouponStatusEnum', """    CouponStatusEnum:
      enum:
      - ACTIVE
      - EXPIRED
      - DISABLED
      - DRAFT"""),

    # CouponWithProducts
    ('CouponWithProducts', """    CouponWithProducts:
      type: object
      properties:
        id:
          type: integer
          format: int64
          readOnly: true
        code:
          type: string
          maxLength: 50
          description: 'Código de cupón. Entre 1 y 50 caracteres. Alfanuméricos, guiones
            bajos.'
          example: SUMMER25
          minLength: 1
          pattern: '^[A-Za-z0-9_]+$'
        discount_type:
          $ref: '#/components/schemas/CouponTypeEnum'
        discount_value:
          type: number
          description: 'Valor del descuento. Si es PERCENTAGE, debe ser entre 1 y 100.
            Si es FIXED_AMOUNT, debe ser positivo.'
          format: double
          minimum: 1
          maximum: 100
        min_order_amount:
          type: number
          description: 'Monto mínimo de compra para aplicar el cupón. Mínimo 0.'
          format: double
          minimum: 0
        max_uses:
          type: integer
          description: 'Máximo de usos del cupón. 0 para uso ilimitado.'
          format: int64
          minimum: 0
        used_count:
          type: integer
          description: 'Número de veces que se ha usado el cupón.'
          format: int64
          readOnly: true
        status:
          $ref: '#/components/schemas/CouponStatusEnum'
        valid_from:
          type: string
          description: 'Fecha de inicio de validez del cupón. Formato ISO 8601.'
          format: date-time
        valid_to:
          type: string
          description: 'Fecha de fin de validez del cupón. Formato ISO 8601.'
          format: date-time
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
      required:
      - code
      - discount_type
      - discount_value
      - min_order_amount"""),

    # CreateCoupon
    ('CreateCoupon', """    CreateCoupon:
      type: object
      properties:
        code:
          type: string
          maxLength: 50
          description: 'Código de cupón. Entre 1 y 50 caracteres. Alfanuméricos, guiones
            bajos.'
          example: SUMMER25
          minLength: 1
          pattern: '^[A-Za-z0-9_]+$'
        discount_type:
          $ref: '#/components/schemas/CouponTypeEnum'
        discount_value:
          type: number
          description: 'Valor del descuento. Si es PERCENTAGE, debe ser entre 1 y 100.
            Si es FIXED_AMOUNT, debe ser positivo.'
          format: double
          minimum: 1
          maximum: 100
        min_order_amount:
          type: number
          description: 'Monto mínimo de compra para aplicar el cupón. Mínimo 0.'
          format: double
          minimum: 0
        max_uses:
          type: integer
          description: 'Máximo de usos del cupón. 0 para uso ilimitado.'
          format: int64
          minimum: 0
        status:
          $ref: '#/components/schemas/CouponStatusEnum'
        valid_from:
          type: string
          description: 'Fecha de inicio de validez del cupón. Formato ISO 8601.'
          format: date-time
        valid_to:
          type: string
          description: 'Fecha de fin de validez del cupón. Formato ISO 8601.'
          format: date-time
      required:
      - code
      - discount_type
      - discount_value
      - min_order_amount"""),

    # PatchedCoupon
    ('PatchedCoupon', """    PatchedCoupon:
      type: object
      properties:
        code:
          type: string
          maxLength: 50
          description: 'Código de cupón. Entre 1 y 50 caracteres. Alfanuméricos, guiones
            bajos.'
          example: SUMMER25
          minLength: 1
          pattern: '^[A-Za-z0-9_]+$'
        discount_type:
          $ref: '#/components/schemas/CouponTypeEnum'
        discount_value:
          type: number
          description: 'Valor del descuento. Si es PERCENTAGE, debe ser entre 1 y 100.
            Si es FIXED_AMOUNT, debe ser positivo.'
          format: double
          minimum: 1
          maximum: 100
        min_order_amount:
          type: number
          description: 'Monto mínimo de compra para aplicar el cupón. Mínimo 0.'
          format: double
          minimum: 0
        status:
          $ref: '#/components/schemas/CouponStatusEnum'
        valid_from:
          type: string
          description: 'Fecha de inicio de validez del cupón. Formato ISO 8601.'
          format: date-time
        valid_to:
          type: string
          description: 'Fecha de fin de validez del cupón. Formato ISO 8601.'
          format: date-time"""),

    # Category
    ('Category', """    Category:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 120
        description:
          type: string
          nullable: true
        emoji:
          type: string
          nullable: true
          maxLength: 20
        is_active:
          type: boolean
          default: true
        is_deleted:
          type: boolean
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
      required:
      - id
      - name"""),

    # CrePro
    ('CrePro', """    CrePro:
      type: object
      description: Serializer para CREAR/EDITAR productos (el vendedor envia datos).
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
        vendor:
          type: string
          format: uuid
          readOnly: true
        categories:
          type: array
          items:
            type: integer
          readOnly: true
        category_names:
          type: array
          items:
            type: string
          readOnly: true
        name:
          type: string
          maxLength: 255
        description:
          type: string
        ai_description:
          type: string
          nullable: true
        price:
          type: string
          format: decimal
          pattern: ^-?\\d{0,8}(?:\\.\\d{0,2})?$
        stock:
          type: integer
          maximum: 9223372036854775807
          minimum: 0
          format: int64
        status:
          $ref: '#/components/schemas/Status308Enum'
        rejection_reason:
          type: string
          nullable: true
        is_featured:
          type: boolean
        images:
          type: array
          items:
            $ref: '#/components/schemas/PImageWrite'
          readOnly: true
        is_deleted:
          type: boolean
      required:
      - categories
      - description
      - id
      - name
      - price
      - vendor"""),

    # PImageWrite
    ('PImageWrite', """    PImageWrite:
      type: object
      properties:
        url_image:
          type: string
        is_main:
          type: boolean
          default: false
      required:
      - url_image"""),

    # PImageRead
    ('PImageRead', """    PImageRead:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        url_image:
          type: string
          readOnly: true
        is_main:
          type: boolean
          readOnly: true
        moderation_status:
          $ref: '#/components/schemas/PImageReadModerationStatusEnum'
        moderation_details:
          type: object
          nullable: true
      required:
      - id
      - url_image
      - moderation_status"""),

    # PImageReadModerationStatusEnum
    ('PImageReadModerationStatusEnum', """    PImageReadModerationStatusEnum:
      enum:
      - PENDING
      - APPROVED
      - REJECTED
      - FLAGGED"""),

    # PatchedCrePro
    ('PatchedCrePro', """    PatchedCrePro:
      type: object
      description: Serializer para CREAR/EDITAR productos (el vendedor envia datos).
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
        vendor:
          type: string
          format: uuid
          readOnly: true
        categories:
          type: array
          items:
            type: integer
          readOnly: true
        category_names:
          type: array
          items:
            type: string
          readOnly: true
        name:
          type: string
          maxLength: 255
        description:
          type: string
        ai_description:
          type: string
          nullable: true
        price:
          type: string
          format: decimal
          pattern: ^-?\\d{0,8}(?:\\.\\d{0,2})?$
        stock:
          type: integer
          maximum: 9223372036854775807
          minimum: 0
          format: int64
        status:
          $ref: '#/components/schemas/Status308Enum'
        rejection_reason:
          type: string
          nullable: true
        is_featured:
          type: boolean
        images:
          type: array
          items:
            $ref: '#/components/schemas/PImageWrite'
          readOnly: true
        is_deleted:
          type: boolean
      required:
      - categories
      - description
      - id
      - name
      - price
      - vendor"""),

    # Status308Enum
    ('Status308Enum', """    Status308Enum:
      enum:
      - PENDING
      - AVAILABLE
      - INACTIVE
      - REJECTED
      - RESERVED
      - SOLD"""),

    # ReadBasicUser
    ('ReadBasicUser', """    ReadBasicUser:
      type: object
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
        username:
          type: string
          readOnly: true
        first_name:
          type: string
          readOnly: true"""),

    # ReadLocation
    ('ReadLocation', """    ReadLocation:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        user:
          type: string
          format: uuid
        latitude:
          type: number
          format: double
        longitude:
          type: number
          format: double
        is_active:
          type: boolean
        date_created:
          type: string
          format: date-time
      required:
      - id
      - user
      - latitude
      - longitude
      - is_active"""),

    # ReadPro
    ('ReadPro', """    ReadPro:
      type: object
      description: Serializer para LEER productos (el cliente ve la lista/detalle).
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
        vendor:
          type: string
          format: uuid
        vendor_name:
          type: string
          readOnly: true
        categories:
          type: array
          items:
            $ref: '#/components/schemas/Category'
          readOnly: true
        category_names:
          type: array
          items:
            type: string
          readOnly: true
        name:
          type: string
          maxLength: 255
        description:
          type: string
        ai_description:
          type: string
          nullable: true
        price:
          type: string
          format: decimal
          pattern: ^-?\\d{0,8}(?:\\.\\d{0,2})?$
        stock:
          type: integer
          maximum: 9223372036854775807
          minimum: 0
          format: int64
        status:
          $ref: '#/components/schemas/Status308Enum'
        rejection_reason:
          type: string
          nullable: true
        is_featured:
          type: boolean
        images:
          type: array
          items:
            $ref: '#/components/schemas/PImageRead'
          readOnly: true
        created_at:
          type: string
          format: date-time
          readOnly: true
        distance:
          type: string
          readOnly: true
        latitude:
          type: string
          readOnly: true
        longitude:
          type: string
          readOnly: true
        is_deleted:
          type: boolean
      required:
      - categories
      - created_at
      - description
      - distance
      - id
      - images
      - latitude
      - longitude
      - name
      - price
      - vendor
      - vendor_name"""),
]

# Build the schemas section
schemas_lines = ['  schemas:\n']
for name, body in schemas_section:
    schemas_lines.append(body + '\n')

# Assemble the full file
output = pre_schemas + schemas_lines + ['\n']
if after_schemas:
    output.extend(after_schemas)

with open(INPUT, 'w', encoding='utf-8') as f:
    f.writelines(output)

print(f"Wrote {len(output)} lines to {INPUT}")

# Validate
import yaml
try:
    with open(INPUT, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    print("YAML VALID!")

    schemas = data['components']['schemas']
    for name in ['CrePro', 'PatchedCrePro', 'ReadPro']:
        props = schemas[name]['properties']
        old_fields = [k for k in props if k in ('category', 'category_name')]
        new_fields = [k for k in props if k in ('categories', 'category_names')]
        if old_fields:
            print(f"  FAIL: {name} still has old fields: {old_fields}")
        elif new_fields:
            print(f"  OK: {name} uses categories/category_names")
        else:
            print(f"  NOTE: {name} fields include: {[k for k in props if 'categor' in k]}")

    all_schema_names = list(schemas.keys())
    print(f"\nTotal schemas: {len(all_schema_names)}")
    print(f"Schemas: {all_schema_names[:10]}...")
except Exception as e:
    print(f"YAML INVALID: {e}")