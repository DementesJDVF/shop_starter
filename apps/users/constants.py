class UserRoles:
    ADMIN = "ADMIN"
    VENDEDOR = "VENDEDOR"
    CLIENTE = "CLIENTE"

    CHOICES = [
        (ADMIN, "Administrador"),
        (VENDEDOR, "Vendedor"),
        (CLIENTE, "Cliente"),
    ]