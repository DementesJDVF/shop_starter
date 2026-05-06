# ===== NUEVO: Sprint IA y Funcionalidad =====
"""
Registro de casos críticos del negocio que dependen de IA.
Modificar solo agregando nuevos casos al diccionario.
"""

IA_CRITICAL_CASES = {
    "recomendacion_producto": {
        "descripcion": "Recomendación personalizada de productos al usuario",
        "severidad": "alta",
        "fallback_permitido": True,
        "fallback_mensaje": "Mostrando productos populares",
    },
    "busqueda_semantica": {
        "descripcion": "Búsqueda de productos por lenguaje natural",
        "severidad": "alta", 
        "fallback_permitido": True,
        "fallback_mensaje": "Usando búsqueda por palabras clave",
    },
    "analisis_resena": {
        "descripcion": "Análisis de reseñas de productos con IA",
        "severidad": "media",
        "fallback_permitido": True,
        "fallback_mensaje": "Mostrando reseñas sin análisis",
    },
}

def validate_critical_ia_case(case_id: str) -> dict:
    """
    Retorna la configuración del caso crítico.
    Retorna None si el caso no existe.
    """
    return IA_CRITICAL_CASES.get(case_id, None)

def is_ia_required(case_id: str) -> bool:
    """Retorna True si el caso no admite fallback"""
    case = IA_CRITICAL_CASES.get(case_id)
    if not case:
        return False
    return not case.get("fallback_permitido", True)
# ===== FIN NUEVO =====
