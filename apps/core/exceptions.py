from rest_framework.views import exception_handler
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Controlador global de excepciones para DRF.
    Retorna un JSON estructurado de la siguiente forma:
    {
        "error": true,
        "message": "Mensaje legible o global de error",
        "code": "ERROR_CODE",
        "details": { ... }
    }
    """
    response = exception_handler(exc, context)

    # Si hay un error que DRF no maneja automáticamente o es 500
    if response is None:
        logger.error(f"Excepción no controlada: {exc}", exc_info=True)
        return None  # Permite que Django envíe el 500 estándar que será interceptado por Axios

    error_payload = {
        "error": True,
        "message": "Ocurrió un error en la solicitud.",
        "code": "API_ERROR",
        "details": {}
    }

    # DRF retorna los detalles en response.data, generalmente como diccionarios o listas.
    if isinstance(response.data, dict):
        # Si DRF trae un "detail" global, lo usamos como mensaje principal
        if "detail" in response.data:
            error_payload["message"] = str(response.data.get("detail"))
            error_payload["code"] = getattr(exc, "default_code", "ERROR")
            response.data.pop("detail", None)
        
        # El resto de llaves suelen ser errores de validación de serializers (detalles)
        if response.data:
            error_payload["details"] = response.data
            if error_payload["message"] == "Ocurrió un error en la solicitud.":
                error_payload["message"] = "Error de validación de datos."
                error_payload["code"] = "VALIDATION_ERROR"
    elif isinstance(response.data, list):
        error_payload["message"] = str(response.data[0])
        error_payload["details"] = {"non_field_errors": response.data}
    else:
        error_payload["message"] = str(response.data)

    response.data = error_payload
    return response
