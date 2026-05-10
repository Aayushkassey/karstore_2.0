from django.shortcuts import redirect, render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment
from django_esewa import EsewaPayment
import uuid
from accounts.models import CustomerActivity
from orders.models import Cart, Order, CartItem

def checkout_process(request):
    if request.method == 'POST':
        amount = request.POST.get('total_price') 
        email = request.user.email
        
        # १. डाटा तान्ने
        is_single = request.POST.get('is_single_checkout') == 'true'
        single_id = request.POST.get('single_product_id', '')
        selected_ids = request.POST.get('selected_item_ids', '')

        # २. Metadata सेभ गर्ने (SINGLE वा CART)
        if is_single:
            meta_data = f"SINGLE:{single_id}"
        elif selected_ids:
            meta_data = f"CART:{selected_ids}"
        else:
            meta_data = "ALL:0"

        uid = uuid.uuid4()
        payment_record = Payment.objects.create(
            uuid=uid,
            user=request.user,
            email=email,
            amount=amount,
            total_amount=amount,
            product_id=meta_data,
            status="PENDING"
        )

        return redirect('payment:initiate_esewa', uuid=payment_record.uuid)

def initiate_esewa(request, uuid):
    order = get_object_or_404(Payment, uuid=uuid)
    
    payment = EsewaPayment(
        product_code="EPAYTEST",
        success_url=f"https://karstore.onrender.com/payment/success/{order.uuid}/",
        failure_url=f"https://karstore.onrender.com/payment/failure/{order.uuid}/",
        amount=order.amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        product_delivery_charge=order.delivery_charge,
        product_service_charge=order.service_charge,
        transaction_uuid=order.uuid,
        secret_key="8gBm/:&EnhH.1/q",
    )
    
    payment.create_signature()
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
            'signed_field_names': signed_fields,
            'signature': payment.signature,
        }
    }
    return render(request, 'payment/confirm_payment.html', context)

def payment_success(request, uuid):
    payment_record = get_object_or_404(Payment, uuid=uuid)
    payment_record.status = "COMPLETE"
    payment_record.save()

    meta = payment_record.product_id
    cart = Cart.objects.get(user=request.user)
    
    if meta.startswith("SINGLE:"):
        p_id = meta.split(":")[1]
        items_to_process = cart.items.filter(product_id=p_id)
    elif meta.startswith("CART:"):
        ids = meta.split(":")[1].split(",")
        items_to_process = cart.items.filter(id__in=ids)
    else:
        items_to_process = cart.items.all()

    item_list = ""
    for item in items_to_process:
        Order.objects.create(
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            final_price=item.product.discounted_price,
            status='Completed'
        )

        product = item.product
        product.stock = max(0, product.stock - item.quantity)
        product.save()

        item_list += f"- {item.product.name} (Qty: {item.quantity}) - Rs. {item.product.discounted_price:.2f}\n"

        CustomerActivity.objects.create(
            user=request.user,
            action='purchase_success',
            product=item.product,
            transaction_id=payment_record.uuid,
        )

    # ✅ Success Email
    subject = f"Order Confirmed - KAR Store (ID: {payment_record.uuid})"
    message = f"Hello {request.user.username},\n\nYour payment was successful! Your order details:\n\n{item_list}\nTotal: Rs. {payment_record.amount:.2f}\n\nThank you for shopping with KAR Store!"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [request.user.email])

    items_to_process.delete()

    return render(request, 'payment/success.html', {'order': payment_record})

def payment_failure(request, uuid):
    payment_record = get_object_or_404(Payment, uuid=uuid)
    payment_record.status = "FAILED"
    payment_record.save()

    meta = payment_record.product_id
    cart = Cart.objects.get(user=request.user)

    if meta.startswith("SINGLE:"):
        p_id = meta.split(":")[1]
        items_to_process = cart.items.filter(product_id=p_id)
    elif meta.startswith("CART:"):
        ids = meta.split(":")[1].split(",")
        items_to_process = cart.items.filter(id__in=ids)
    else:
        items_to_process = cart.items.all()

    for item in items_to_process:
        Order.objects.create(
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            final_price=item.product.discounted_price,
            status='Cancelled'
        )
        CustomerActivity.objects.create(
            user=request.user,
            action='purchase_failed',
            product=item.product,
            transaction_id=payment_record.uuid,
        )

    # ✅ Failure Email
    subject = "Payment Failed - KAR Store"
    message = f"Hi {request.user.username},\n\nWe couldn't process your payment for Transaction ID: {payment_record.uuid}. Please try again later."
    send_mail(subject, message, settings.EMAIL_HOST_USER, [request.user.email])

    return render(request, 'payment/failure.html', {'order': payment_record})