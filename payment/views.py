from django.shortcuts import redirect, render, get_object_or_404
from .models import Payment  # Timro naya payment app ko model
from django_esewa import EsewaPayment
import uuid
from accounts.models import CustomerActivity
from orders.models import Cart
def checkout_process(request):
    if request.method == 'POST':
        # Cart bata data tanni (e.g., total amount)
        amount = request.POST.get('total_price') 
        email = request.user.email
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        # New Payment record (Status: PENDING)
        uid = uuid.uuid4()
        payment_record = Payment.objects.create(
            uuid=uid,
            user=request.user,
            email=email,
            amount=amount,
            total_amount=amount,
            status="PENDING"
        )

        # Trace in CustomerActivity
        # CustomerActivity.objects.create(user=request.user, action="Initiated Payment", transaction_id=uid)

        return redirect('payment:initiate_esewa', uuid=payment_record.uuid)

def initiate_esewa(request, uuid):
    order = get_object_or_404(Payment, uuid=uuid)
    
    payment = EsewaPayment(
        product_code="EPAYTEST",
        success_url=f"http://127.0.0.1:8000/payment/success/{order.uuid}/",
        failure_url=f"http://127.0.0.1:8000/payment/failure/{order.uuid}/",
        amount=order.amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        product_delivery_charge=order.delivery_charge,
        product_service_charge=order.service_charge,
        transaction_uuid=order.uuid,
        secret_key="8gBm/:&EnhH.1/q",
    )
    
    payment.create_signature()
    
    # eSewa V2 ko lagi signature garine fields ko list (Standard fixed hunchha)
    signed_fields = "total_amount,transaction_uuid,product_code"

    context = {
        'esewa_form_fields': {
            'amount': payment.amount,
            'tax_amount': payment.tax_amount,
            'total_amount': payment.total_amount,
            'transaction_uuid': payment.transaction_uuid,
            'product_code': payment.product_code,
            'product_service_charge': payment.product_service_charge,
            'product_delivery_charge': payment.product_delivery_charge,
            'success_url': payment.success_url,
            'failure_url': payment.failure_url,
            'signed_field_names': signed_fields, # Yo manual halda error audaina
            'signature': payment.signature,
        }
    }
    return render(request, 'payment/confirm_payment.html', context)

def payment_success(request, uuid):
    order = get_object_or_404(Payment, uuid=uuid)
    order.status = "COMPLETE"
    order.save()

    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all()
    for item in cart_items:
        CustomerActivity.objects.create(
            user=request.user,
            action='purchase_success',
            product_id=str(item.product.id),   # ✅ FK object
            transaction_id=order.uuid,
        )

    cart.items.all().delete()

    return render(request, 'payment/success.html', {'order': order})
def payment_failure(request, uuid):
    order = get_object_or_404(Payment, uuid=uuid)
    order.status = "FAILED"
    order.save()

    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all()
    for item in cart_items:
        CustomerActivity.objects.create(
            user=request.user,
            action='purchase_failed',
            product_id=str(item.product.id), 
            transaction_id=order.uuid,
        )

    return render(request, 'payment/failure.html', {'order': order})