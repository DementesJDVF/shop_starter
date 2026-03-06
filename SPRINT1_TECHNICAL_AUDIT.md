# Auditoría Técnica Sprint 1 (SHOPSTARTER MVP)

## 1) Diagnóstico General del Sprint 1
- **Estado global:** **FAIL**
- **Resultado:** La implementación de Sprint 1 no está lista para producción.
- **Clasificación:** **RIESGO ARQUITECTÓNICO ALTO**

## 2) Evaluación por HU

### HU01 – Registro y Autenticación por Rol
- **Estado:** **FAIL**
- Hallazgos:
  - Existe Custom User y está configurado en `AUTH_USER_MODEL`. 
  - El modelo `User` define `role` dos veces (duplicación de campo).
  - Existe estado de usuario (`status`) y `email` único.
  - El password se crea con `create_user` (hash correcto).
  - JWT tiene configuración declarada con typo (`SSIMPLE_JWT`), por lo que no aplica la configuración esperada.
  - Login retorna `access_token` y `refresh_token`.
  - Endpoints de registro/login/me existen.
  - Riesgo de seguridad: en registro se permite enviar `role` desde cliente (potencial auto-escalación a ADMIN).
  - Los tests de autenticación existen, pero no con los nombres exactos solicitados en HU.

### HU02 – Control de Permisos y Middleware
- **Estado:** **FAIL**
- Hallazgos:
  - Existen permisos por rol (`IsAdmin`, `IsVendor`, `IsClient`, etc.).
  - `AdminOnlyView` usa permiso de rol admin.
  - Middleware de usuario actual/IP existe (`CurrentUserMiddleware`) y bloqueo de usuario inactivo existe.
  - Existe middleware adicional `RoleRequiredMiddleware` pero no está registrado en `MIDDLEWARE`.
  - Cobertura parcial de pruebas; no aparece el test con nombre exacto `test_vendor_cannot_access_admin_features`.
  - Inconsistencia potencial: test espera 401 para inactivo, middleware devuelve 403.

### HU03 – BaseModel + Soft Delete
- **Estado:** **FAIL**
- Hallazgos:
  - `BaseModel` incluye `created_at` con índice, `updated_at`, `is_deleted` con índice.
  - Managers `objects` y `all_objects` están implementados.
  - Métodos `delete()` y `restore()` implementados.
  - `hard_delete()` está defectuoso: usa variables `using` y `keep_parents` no definidas.
  - Soft delete no está transversal en entidades críticas: `Product` hereda `BaseModel`, pero `Vendor` y `Order` no.
  - Existe test suite de soft delete, pero no usa exactamente los nombres solicitados en HU.

### HU04 – Auditoría Transversal
- **Estado:** **FAIL**
- Hallazgos:
  - `AuditLog` contiene campos solicitados (incluyendo `content_type`, `object_id`, `previous_data`, `new_data`, `ip_address`, `created_at`).
  - Índices solicitados por HU no están completos en estado final de migraciones: se removieron índices `user_id` y `content_type + object_id`.
  - Registro de `CREATE` y `LOGIN` está implementado desde `UserService`.
  - Registro de `SOFT_DELETE` y `RESTORE` está implementado en `SoftDeleteService`.
  - `ROLE_CHANGE` está implementado en servicio.
  - No hay mecanismo transversal automático para `UPDATE` en entidades; depende de uso explícito de servicios.
  - Endpoint de logs está restringido a ADMIN.
  - Admin de auditoría es readonly para add/change, pero no bloquea delete explícitamente.
  - Existen tests HU04 solicitados con esos nombres.

## 3) Errores críticos encontrados
1. Duplicación de campo `role` en `User`.
2. Configuración JWT inválida por typo (`SSIMPLE_JWT` en vez de `SIMPLE_JWT`).
3. `hard_delete()` en `BaseModel` rompe en runtime por variables no definidas.
4. Índices HU04 requeridos no están completos tras migraciones (faltan `user_id` y `content_type + object_id`).
5. Registro permite asignación directa de rol por payload cliente (riesgo de privilegios).
6. Soft delete no aplicado de forma transversal a entidades críticas.

## 4) Riesgos a mediano plazo
- Deriva arquitectónica por separación incompleta de capas entre apps.
- Inconsistencias de seguridad por elevación de rol en registro.
- Riesgo forense/auditoría por ausencia de índices requeridos y trazabilidad no 100% transversal.
- Riesgo operacional por fallas latentes (`hard_delete`) al ejecutar mantenimiento de datos.

## 5) Problemas de seguridad
- Posible auto-asignación de rol privilegiado al registrarse.
- Middleware de rol no integrado (`RoleRequiredMiddleware` no activo).
- Política de bloqueo de usuarios inactivos inconsistente con pruebas y potencial UX/API contract drift.

## 6) Problemas de rendimiento
- Índices de auditoría incompletos respecto al diseño objetivo de consultas por entidad + timeline.
- Sin validación de `EXPLAIN ANALYZE` en PostgreSQL dentro del entorno actual.

## 7) Recomendaciones concretas
1. Corregir `SIMPLE_JWT` y validar expiraciones/rotación efectivas.
2. Eliminar duplicación de `role` en `User` y consolidar constraints/default.
3. Corregir `hard_delete(self, using=None, keep_parents=False)`.
4. Restringir registro para forzar `role=CLIENTE` (o whitelist por contexto admin).
5. Re-crear índices HU04 requeridos: `user_id`, `content_type+object_id`, `content_type+object_id+created_at DESC`, `action_type`, `created_at`.
6. Hacer soft delete transversal real en entidades críticas (`Vendor`, `Order`, etc.).
7. Bloquear delete en admin de auditoría (`has_delete_permission=False`).
8. Añadir tests faltantes por nombre/escenario HU02 y HU03 para cumplir contrato de sprint.
9. Ejecutar `EXPLAIN (ANALYZE, BUFFERS)` en staging con PostgreSQL real y adjuntar evidencia.

## 8) Nivel de preparación
- **DESARROLLO** ✅
- **STAGING** ❌
- **PRODUCCIÓN** ❌

---

## Evidencia técnica revisada (resumen)
- Modelo/seguridad/auth: `apps/users/models.py`, `apps/users/serializers.py`, `apps/users/views.py`, `apps/users/api/auth_views.py`, `config/settings/base.py`.
- Permisos/middleware: `apps/users/permissions.py`, `apps/core/middleware.py`, `apps/users/middleware.py`.
- Soft delete: `apps/core/models/base.py`, `apps/core/models/managers.py`, `apps/core/application/services.py`, entidades de dominio (`products`, `vendors`, `orders`).
- Auditoría: `apps/audit/infrastructure/models.py`, `apps/audit/application/services.py`, `apps/audit/api/viewsets.py`, `apps/audit/admin.py`, migraciones `apps/audit/migrations/`.
- Tests: `apps/users/tests/tests.py`, `apps/users/tests/test_permissions.py`, `apps/core/tests/test_soft_delete_core.py`, `apps/audit/tests/tests.py`.
