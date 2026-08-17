import os
from django.conf import settings
from .models import Payment

class RazorpayMockOrder:
    def __init__(self, order_id, amount, currency="INR"):
        self.id = order_id
        self.amount = amount
        self.currency = currency
        self.status = "created"

class PaymentService:
    @staticmethod
    def initialize_payment(booking, method):
        """
        Creates a payment record linked to the booking.
        For CASH_ON_ARRIVAL, status defaults to PENDING.
        For online payment, registers the transaction.
        """
        # Delete existing payment if any to avoid uniqueness clashes
        Payment.objects.filter(booking=booking).delete()
        
        payment = Payment.objects.create(
            booking=booking,
            payment_method=method,
            amount=booking.total_price,
            status=Payment.PaymentStatus.PENDING
        )
        return payment

    @staticmethod
    def process_cash_payment(payment):
        """Mark Cash on Arrival payment ready (remains pending until actual arrival/handover)"""
        payment.status = Payment.PaymentStatus.PENDING
        payment.save()
        return True

    @staticmethod
    def generate_online_order(booking):
        """
        Generates Razorpay order details.
        If Razorpay API keys are configured, it interacts with razorpay client.
        Otherwise, it simulates a mock order detail dictionary.
        """
        amount_paise = int(booking.total_price * 100)
        key_id = os.environ.get('RAZORPAY_KEY_ID', '')
        key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')

        if key_id and key_secret:
            try:
                import razorpay
                client = razorpay.Client(auth=(key_id, key_secret))
                data = {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": f"receipt_{booking.id}",
                    "payment_capture": 1
                }
                razorpay_order = client.order.create(data=data)
                return {
                    "order_id": razorpay_order['id'],
                    "amount": booking.total_price,
                    "key_id": key_id,
                    "mock": False
                }
            except Exception as e:
                # Log or fallback to mock in development if import/conn fails
                pass
        
        # Return mockup structure for easy client side handling
        import uuid
        mock_id = f"order_mock_{uuid.uuid4().hex[:12]}"
        return {
            "order_id": mock_id,
            "amount": booking.total_price,
            "key_id": "mock_key_id",
            "mock": True
        }

    @staticmethod
    def verify_online_payment(payment, gateway_payment_id, gateway_order_id, gateway_signature):
        """
        Verifies signature. If valid, marks payment as COMPLETED.
        """
        key_id = os.environ.get('RAZORPAY_KEY_ID', '')
        key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')

        if gateway_order_id.startswith("order_mock_"):
            # Auto approve mock payments in dev
            payment.transaction_id = gateway_payment_id
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.save()
            return True

        if key_id and key_secret:
            try:
                import razorpay
                client = razorpay.Client(auth=(key_id, key_secret))
                params_dict = {
                    'razorpay_order_id': gateway_order_id,
                    'razorpay_payment_id': gateway_payment_id,
                    'razorpay_signature': gateway_signature
                }
                client.utility.verify_payment_signature(params_dict)
                
                payment.transaction_id = gateway_payment_id
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.save()
                return True
            except Exception:
                payment.status = Payment.PaymentStatus.FAILED
                payment.save()
                return False

        return False
