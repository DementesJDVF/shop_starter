class UserRoles:
    ADMIN = "ADMIN"
    VENDOR = "VENDEDOR"
    CUSTOMER = "CLIENTE"

    VENDEDOR = VENDOR
    CLIENTE = CUSTOMER

    CHOICES = [
        (ADMIN, "Administrador"),
        (VENDOR, "Vendedor"),
        (CUSTOMER, "Cliente"),
    ]

    SELF_ASSIGNABLE = [VENDOR, CUSTOMER]
