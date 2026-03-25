from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.application.services import AuditService
from apps.audit.infrastructure.models import AuditLog
from apps.core.application.services import SoftDeleteService
from apps.products.models import Product
from apps.vendors.models import Vendor

User = get_user_model()


class AuditHU04Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123"

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password=self.password,
            role="ADMIN",
        )
        self.client_user = User.objects.create_user(
            username="cliente",
            email="cliente@test.com",
            password=self.password,
            role="CLIENTE",
        )

        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@test.com",
            password=self.password,
            role="VENDEDOR",
        )
        self.vendor = Vendor.objects.create(user=self.vendor_user, location_type="FIJA")

    def test_register_creates_audit_log(self):
        payload = {
            "nombre_completo": "Nuevo Usuario",
            "correo_electronico": "newuser@test.com",
            "tipo_documento": "CC",
            "numero_documento": "4455667788",
            "fecha_nacimiento": "1992-04-05",
            "fecha_expedicion": "2010-04-05",
            "telefono": "+573155551212",
            "direccion": "Calle 50 #40-30",
            "nombre_negocio": "Negocio Nuevo",
            "tipos_producto": "Abarrotes",
            "contrasena": self.password,
            "confirmar_contrasena": self.password,
            "rol": "VENDEDOR",
        }

        response = self.client.post("/api/auth/register/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(action_type=AuditLog.ActionType.CREATE, user__email="newuser@test.com").exists()
        )

    def test_login_creates_audit_log(self):
        payload = {"email": self.client_user.email, "password": self.password}

        response = self.client.post("/api/auth/login/", payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(action_type=AuditLog.ActionType.LOGIN, user=self.client_user).exists()
        )

    def test_soft_delete_creates_audit_log(self):
        product = Product.objects.create(
            name="Prod 1",
            price=10,
            stock=5,
            vendor=self.vendor,
        )

        SoftDeleteService.soft_delete(user=self.admin, instance=product, ip_address="127.0.0.1")

        self.assertTrue(
            AuditLog.objects.filter(
                action_type=AuditLog.ActionType.SOFT_DELETE,
                object_id=str(product.id),
            ).exists()
        )

    def test_restore_creates_audit_log(self):
        product = Product.objects.create(
            name="Prod 2",
            price=11,
            stock=5,
            vendor=self.vendor,
        )
        SoftDeleteService.soft_delete(user=self.admin, instance=product, ip_address="127.0.0.1")

        SoftDeleteService.restore(user=self.admin, instance=product, ip_address="127.0.0.1")

        self.assertTrue(
            AuditLog.objects.filter(
                action_type=AuditLog.ActionType.RESTORE,
                object_id=str(product.id),
            ).exists()
        )

    def test_non_admin_cannot_access_audit_logs(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get("/api/audit/logs/")

        self.assertEqual(response.status_code, 403)

    def test_role_change_creates_audit_log(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/users/{self.client_user.id}/role/",
            {"role": "VENDEDOR"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action_type=AuditLog.ActionType.ROLE_CHANGE,
                object_id=str(self.client_user.id),
            ).exists()
        )

    def test_status_change_with_anonymous_actor_does_not_crash(self):
        AuditService.log_status_change(
            user=AnonymousUser(),
            instance=self.client_user,
            previous_status=self.client_user.status,
            ip_address="127.0.0.1",
        )

        log = AuditLog.objects.filter(
            action_type=AuditLog.ActionType.STATUS_CHANGE,
            object_id=str(self.client_user.id),
        ).latest("created_at")
        self.assertIsNone(log.user)

    def test_base_model_create_is_audited_automatically(self):
        product = Product.objects.create(
            name="Prod signal",
            price=10,
            stock=2,
            vendor=self.vendor,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                action_type=AuditLog.ActionType.CREATE,
                object_id=str(product.id),
            ).exists()
        )

    def test_base_model_update_is_audited_automatically(self):
        product = Product.objects.create(
            name="Prod signal update",
            price=10,
            stock=2,
            vendor=self.vendor,
        )
        product.stock = 4
        product.save(update_fields=["stock"])

        self.assertTrue(
            AuditLog.objects.filter(
                action_type=AuditLog.ActionType.UPDATE,
                object_id=str(product.id),
            ).exists()
        )
