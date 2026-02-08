import logging
from decimal import Decimal
from django.conf import settings
from rest_framework import status
import mercadopago

logger = logging.getLogger(__name__)

class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    def create_preference(self, title, description, amount, external_reference, payer_email):
        """Create a payment preference in MercadoPago"""
        preference_data = {
            "items": [
                {
                    "title": title,
                    "description": description,
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": float(amount.quantize(Decimal('0.01'))),
                }
            ],
            "payer": {
                "email": payer_email,
            },
            "external_reference": external_reference,
            "back_urls": {
                "success": settings.PAYMENT_SUCCESS_URL,
                "failure": settings.PAYMENT_FAILURE_URL,
                "pending": settings.PAYMENT_PENDING_URL,
            },
            "notification_url": settings.PAYMENT_WEBHOOK_URL,
            "auto_return": "approved",
        }

        try:
            preference_response = self.sdk.preference().create(preference_data)
            response = preference_response.get("response", {})

            if preference_response.get("status") == status.HTTP_201_CREATED:
                logger.info(
                    'MercadoPago preference created: %s',
                    response.get("id")
                )
                return {
                    "preference_id": response.get("id"),
                    "init_point": response.get("init_point"),
                    "sandbox_init_point": response.get("sandbox_init_point"),
                }
            else:
                logger.error(
                    'MercadoPago preference creation failed: %s',
                    preference_response
                )
                return {"error": response.get("message", "Unknown error")}

        except Exception as e:
            logger.exception('MercadoPago preference creation exception')
            return {"error": str(e)}

    def get_payment(self, payment_id):
        """Get payment details from MercadoPago"""
        try:
            payment_response = self.sdk.payment().get(payment_id)
            response = payment_response.get("response", {})

            if payment_response.get("status") == status.HTTP_200_OK:
                return response
            else:
                logger.error('MercadoPago get payment failed: %s', payment_response)
                return {"error": response.get("message", "Unknown error")}

        except Exception as e:
            logger.exception('MercadoPago get payment exception')
            return {"error": str(e)}

    def get_payment_status(self, payment_id):
        """Get the status of a payment"""
        payment = self.get_payment(payment_id)

        if "error" in payment:
            return "error"
        
        return payment.get("status", "unknown")

    def search_payments_by_reference(self, external_reference):
        """Search for payments by external reference"""
        try:
            filters = {
                "external_reference": external_reference
            }
            search_response = self.sdk.payment().search(filters)
            response = search_response.get("response", {})

            if search_response.get("status") == status.HTTP_200_OK:
                return response.get("results", [])
            else:
                logger.error('MercadoPago search payments failed: %s', search_response)
                return []

        except Exception as e:
            logger.exception('MercadoPago search payments exception')
            return []


def get_mercadopago_service():
    """Factory function to get MercadoPago service instance"""
    return MercadoPagoService()
