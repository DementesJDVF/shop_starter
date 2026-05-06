# ===== NUEVO: Sprint IA y Funcionalidad =====
import time
import threading
from django.test import TestCase
from ..utils.ia_safe_wrapper import safe_ia_call

def mock_ia_lenta():
    """Simula una IA lenta"""
    time.sleep(0.5)
    return "respuesta IA"

def mock_ia_fallida():
    """Simula una IA que falla"""
    raise Exception("IA no disponible")

class IAStressTest(TestCase):
    
    def test_multiples_llamadas_concurrentes(self):
        """Verifica que múltiples llamadas concurrentes no rompan el sistema"""
        resultados = []
        
        def llamar_ia():
            resultado = safe_ia_call(mock_ia_lenta, fallback="fallback")
            resultados.append(resultado)
        
        hilos = [threading.Thread(target=llamar_ia) for _ in range(10)]
        for h in hilos: h.start()
        for h in hilos: h.join()
        
        self.assertEqual(len(resultados), 10)
    
    def test_fallback_cuando_ia_falla(self):
        """Verifica que el fallback se retorna sin lanzar excepción"""
        resultado = safe_ia_call(mock_ia_fallida, fallback="respuesta_segura")
        self.assertEqual(resultado, "respuesta_segura")
    
    def test_tiempo_de_respuesta(self):
        """Verifica que la IA responde en tiempo razonable"""
        inicio = time.time()
        safe_ia_call(mock_ia_lenta, fallback=None)
        duracion = time.time() - inicio
        self.assertLess(duracion, 3.0, "La IA tardó más de 3 segundos")
# ===== FIN NUEVO =====
