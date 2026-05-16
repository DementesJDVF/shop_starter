"""
Custom FilterSets for Products app with M2M category support.
"""
import django_filters
from apps.products.models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """
    Filtro personalizado para Product que soporta múltiples categorías
    con modo AND estricto (productos que pertenezcan a TODAS las categorías seleccionadas).
    """
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name='categories',
        queryset=Category.objects.all(),
        conjoined=True,  # AND estricto: solo productos con TODAS las categorías
        label='Categorías (AND)',
    )

    categories_any = django_filters.ModelMultipleChoiceFilter(
        field_name='categories',
        queryset=Category.objects.all(),
        conjoined=False,  # OR: productos con CUALQUIERA de las categorías
        distinct=True,  # Evita duplicados por joins M2M múltiples
        label='Categorías (OR)',
    )

    status = django_filters.MultipleChoiceFilter(
        choices=Product.ProductStatus.choices,
    )

    class Meta:
        model = Product
        fields = ['status']