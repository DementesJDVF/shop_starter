# HU04 – Auditoría Transversal (Sprint 1 MVP SHOPSTARTER)

## Diagnóstico General
**FAIL**

La implementación actual **no cumple** HU04 de forma integral en capa de dominio, aplicación, exposición API, seguridad operativa ni cobertura de pruebas.

## Checklist técnico punto por punto

- [x] Existe modelo `AuditLog` en módulo de infraestructura.
- [ ] Catálogo de acciones críticas completo y alineado a HU04 (`RESTORE` no existe como `ActionType`; `DELETE` existe pero no se registra en flujos revisados).
- [ ] Registro transversal real de `CREATE`, `UPDATE`, `DELETE`, `SOFT_DELETE`, `RESTORE`, `LOGIN`, `ROLE_CHANGE`.
- [~] Persistencia de `usuario`, `fecha`, `IP`, `previous_data`, `new_data` (campos existen, pero el uso no es consistente en todos los casos).
- [~] Integración real con `BaseModel` (hay herencia, pero también duplicidad de implementaciones de `BaseModel` y soft delete fuera de servicio).
- [ ] Uso obligatorio de Service Layer sin lógica de auditoría en views.
- [~] Índices definidos para búsquedas por entidad y orden temporal (el índice compuesto requerido sí está modelado; hay desalineaciones de migración/modelo y ausencia de evidencia de plan de ejecución real).
- [ ] Endpoint de logs operativo y protegido solo ADMIN (la protección existe en permiso, pero endpoint no está efectivamente expuesto y el viewset tiene referencia no resuelta).
- [ ] Tests automatizados HU04 solicitados presentes y validando creación real de logs.

## Hallazgos técnicos por área

### 1) Modelo `AuditLog`
- `AuditLog` incluye `user`, `created_at` (heredado), `ip_address`, `previous_data`, `new_data`, relación genérica por `content_type` + `object_id` y `object_repr`.
- Meta incluye índice compuesto `("content_type", "object_id", "-created_at")` y orden descendente por `created_at`.
- Gap HU04: no existe `ActionType.RESTORE`; por tanto no hay trazabilidad explícita de restauraciones.

### 2) Integración con `SoftDeleteService`, `UserService` y middleware
- `SoftDeleteService.soft_delete` intenta auditar soft delete, pero invoca `AuditService.log_soft_delete(...)` con parámetros `previous_data` y `new_data` que **no forman parte de la firma** de `log_soft_delete`; esto deriva en error de ejecución cuando se invoque ese flujo.
- `UserService.change_role` registra cambio de rol usando `log_update` (no `ROLE_CHANGE`), por lo que la semántica de evento crítico HU04 queda degradada.
- Middleware de contexto sólo resuelve usuario en thread-local; no hay middleware equivalente para captura transversal de IP y la IP se toma manualmente en views específicas.

### 3) Service Layer vs Views
- Registro de auditoría para registro de usuario (`CREATE`) y login (`LOGIN`) está implementado en views (`RegisterView`, `LoginView`) en lugar de concentrarse en servicios de aplicación.
- Esto rompe el principio de transversalidad y el requerimiento explícito de evitar lógica de dominio/aplicación en views.

### 4) Migraciones y coherencia
- `content_type` existe en modelo y migraciones (`content_type_id` se materializa por FK de Django).
- Se observa evolución de índices: creación inicial, ajuste a índice compuesto con orden por `-created_at`, y eliminación de índices anteriores.
- Riesgo de coherencia: existe duplicidad de implementación de `BaseModel` (`apps/core/models.py` y `apps/core/models/base.py`) con diferencias estructurales; el `AuditLog` hereda de una variante distinta a la usada para generar ciertos esquemas históricos, aumentando riesgo de drift.

### 5) Rendimiento (consulta objetivo)
Consulta objetivo:
```sql
SELECT *
FROM audit_auditlog
WHERE content_type_id = X AND object_id = Y
ORDER BY created_at DESC;
```
- A nivel de definición de modelo/migración, existe índice compuesto compatible con ese patrón de filtro + orden.
- No hay evidencia ejecutable de `EXPLAIN ANALYZE` en PostgreSQL en este entorno (dependencias de runtime no instaladas), por lo que la validación queda parcial en nivel estático.

### 6) Seguridad de endpoint y admin
- Existe permiso `IsAdminUserRole` restringiendo acceso a `request.user.role == "ADMIN"`.
- `AuditLogAdmin` está configurado read-only (sin add/change).
- Sin embargo, el endpoint API de auditoría no está publicado en `config/urls.py` y `apps/audit/urls.py` está vacío; además, `AuditLogViewSet` referencia `StandardResultsSetPagination` sin import/definición visible, dejando el endpoint no funcional aunque se enrute.

### 7) Cobertura de tests HU04
- No se encontraron pruebas implementadas para:
  - `test_register_creates_audit_log`
  - `test_login_creates_audit_log`
  - `test_soft_delete_creates_audit_log`
  - `test_restore_creates_audit_log`
  - `test_non_admin_cannot_access_audit_logs`
- `apps/audit/tests/tests.py` está vacío (stub de `TestCase`).

## Errores encontrados
1. **Incompatibilidad de firma** entre `SoftDeleteService.soft_delete` y `AuditService.log_soft_delete`.
2. **Uso incorrecto del tipo de evento** en cambio de rol (`log_update` vs `ROLE_CHANGE`).
3. **Lógica de auditoría en views** (`RegisterView`, `LoginView`) fuera de Service Layer.
4. **Endpoint de auditoría no operativo** (ruteo ausente + símbolo de paginación no definido).
5. **Sin trazabilidad de RESTORE** como evento crítico explícito.
6. **Suite de pruebas HU04 inexistente**.
7. **Duplicidad de BaseModel** con potencial drift arquitectónico.

## Riesgos arquitectónicos
- **Incumplimiento regulatorio/forense** por pérdida de eventos críticos o semántica inconsistente.
- **Falsa sensación de cobertura** al existir modelo de auditoría pero no flujo transversal completo.
- **Riesgo de regresiones** por ausencia de tests de contrato HU04.
- **Riesgo operativo** al depender de lógica en views, difícil de reutilizar y auditar en procesos no HTTP.
- **Riesgo de mantenimiento** por duplicidad de modelo base y divergencia de comportamientos de soft delete.

## Recomendaciones concretas
1. Añadir `ActionType.RESTORE` y método `AuditService.log_restore`.
2. Corregir `SoftDeleteService` para usar firmas válidas y centralizar soft-delete/restore en servicios transaccionales.
3. Incorporar `AuditService.log_role_change` y reemplazar `log_update` en `UserService.change_role`.
4. Mover auditoría de `RegisterView` y `LoginView` a servicios de aplicación; views sólo orquestan request/response.
5. Implementar middleware o utilitario transversal para extracción normalizada de IP (`X-Forwarded-For` + `REMOTE_ADDR`) y propagarla a la Service Layer.
6. Publicar endpoint de auditoría en `apps/audit/urls.py` + `config/urls.py`; corregir dependencia de paginación (`StandardResultsSetPagination`).
7. Crear test suite HU04 mínima obligatoria con asserts de persistencia real de filas en `AuditLog` y control de permisos admin/no-admin.
8. Unificar una sola implementación canónica de `BaseModel`/querysets/managers y alinear migraciones.
9. Ejecutar validación de performance en entorno PostgreSQL real con `EXPLAIN (ANALYZE, BUFFERS)` sobre la consulta objetivo.

## Nivel de preparación
**DEV**

No apto para STAGING/PRODUCCIÓN hasta cerrar los gaps funcionales, de seguridad operativa y de pruebas indicados arriba.
