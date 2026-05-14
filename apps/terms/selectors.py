from django.conf import settings

from apps.terms.models import TermsAcceptance, TermsContent


DEFAULT_TERMS_CONTENT = """ShopStarter - Términos y Condiciones de Privacidad

1. Uso de la plataforma: El usuario se compromete a utilizar ShopStarter únicamente para fines lícitos.
2. Responsabilidades: ShopStarter no se hace responsable por el contenido publicado por vendedores terceros.
3. Privacidad: Los datos personales son tratados conforme a la política de privacidad vigente.
4. Aceptación: Al registrarse o iniciar sesión, el usuario acepta estos términos en su versión actual.
"""


def get_latest_acceptance(user):
    return TermsAcceptance.objects.filter(user=user).order_by("-accepted_at").first()


def get_terms_content(version):
    terms_content = TermsContent.objects.filter(
        version=version,
        is_active=True,
    ).first()

    if terms_content:
        return terms_content

    terms_content = getattr(settings, "SHOPSTARTER_TERMS_CONTENT", {})
    return terms_content.get(version, DEFAULT_TERMS_CONTENT)
