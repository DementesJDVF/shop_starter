# ===== NUEVO: Sprint IA y Funcionalidad =====
from .ia_error_notifier import notify_ia_failure

def safe_ia_call(ia_function, *args, fallback=None, context=None, **kwargs):
    """
    Wrapper seguro para cualquier llamada a IA.
    Si falla, retorna el fallback sin romper el flujo.
    
    Uso:
        resultado = safe_ia_call(mi_funcion_ia, param1, fallback="Respuesta por defecto")
    """
    try:
        return ia_function(*args, **kwargs)
    except Exception as e:
        notify_ia_failure(e, context=context)
        return fallback
# ===== FIN NUEVO =====
