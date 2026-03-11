# Sprint 7 - Gestión de Usuarios

Historia de Usuario:
S7-HU01 Gestión usuarios

Como administrador
Quiero gestionar los usuarios de la plataforma
Para controlar accesos, roles y estado de las cuentas.

## Funcionalidades implementadas

- Registro de usuarios
- Login de usuarios
- Endpoint `/api/auth/me`
- Control de roles (ADMIN, VENDEDOR, CLIENTE)
- Validación de acceso a rutas administrativas
- Gestión de usuarios desde Django Admin

## Pruebas realizadas

- ADMIN puede acceder a `/api/admin/test`
- VENDEDOR recibe `403 Forbidden`
- CLIENTE recibe `403 Forbidden`
- Usuarios pueden autenticarse correctamente