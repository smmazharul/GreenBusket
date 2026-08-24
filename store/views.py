from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
import json
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from .models import Category, Product, Order, OrderItem
from .cart import Cart

def home(request):
    categories = Category.objects.filter(is_active=True)
    featured_products = Product.objects.filter(is_active=True)[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'products': featured_products
    })

def shop(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    products = Product.objects.filter(is_active=True)
    active_category = None
    
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)
        
    if search_query:
        from django.db.models import Q
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
        
    return render(request, 'store/shop.html', {
        'products': products,
        'active_category': active_category,
        'search_query': search_query,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'store/product_detail.html', {
        'product': product
    })

def tracking(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        if phone:
            orders = Order.objects.filter(phone=phone).order_by('-created_at')
            if orders.exists():
                return render(request, 'store/tracking_result.html', {'orders': orders, 'phone': phone})
            else:
                return render(request, 'store/tracking.html', {'error': 'No orders found for this phone number.'})
            
    return render(request, 'store/tracking.html')

def cart_api(request):
    cart = Cart(request)
    return JsonResponse(cart.get_cart_data())

def cart_add(request):
    cart = Cart(request)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            product = get_object_or_404(Product, id=product_id)
            cart.add(product=product, quantity=quantity)
            return JsonResponse(cart.get_cart_data())
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def cart_update(request):
    cart = Cart(request)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity')
            product = get_object_or_404(Product, id=product_id)
            cart.update(product=product, quantity=quantity)
            return JsonResponse(cart.get_cart_data())
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def buy_now(request, product_id):
    if request.method == 'POST':
        quantity = request.POST.get('quantity', 1)
        product = get_object_or_404(Product, id=product_id)
        request.session['buy_now_item'] = {
            'product_id': product.id,
            'quantity': int(quantity),
            'price': str(product.price)
        }
        return redirect('checkout')
    return redirect('shop')

def checkout(request):
    buy_now_item = request.session.get('buy_now_item')
    cart = Cart(request)
    
    if buy_now_item:
        product = get_object_or_404(Product, id=buy_now_item['product_id'])
        items = [{
            'product': product,
            'quantity': buy_now_item['quantity'],
            'price': buy_now_item['price'],
            'total': float(buy_now_item['price']) * buy_now_item['quantity']
        }]
        subtotal = items[0]['total']
    else:
        cart_data = cart.get_cart_data()
        if not cart_data['items']:
            return redirect('shop')
        items = []
        for item in cart_data['items']:
            product = get_object_or_404(Product, id=item['product_id'])
            items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': item['price'],
                'total': float(item['price']) * item['quantity']
            })
        subtotal = float(cart_data['total_price'])
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        district = request.POST.get('district', '')
        
        delivery_charge = 60 if district.strip().lower() == 'dhaka' else 120
        total_amount = subtotal + delivery_charge
        
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        last_order = Order.objects.order_by('-id').first()
        seq = (last_order.id + 1) if last_order else 1
        order_id_str = f"CHB-{date_str}-{seq:03d}"
        
        order = Order.objects.create(
            order_id=order_id_str,
            customer_name=name,
            phone=phone,
            address=address,
            district=district,
            total_amount=total_amount,
            delivery_charge=delivery_charge
        )
        
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )
            # Deduct stock
            item['product'].stock -= item['quantity']
            item['product'].save()
            
        if 'buy_now_item' in request.session:
            del request.session['buy_now_item']
        else:
            cart.clear()
            
        return redirect('order_success', order_id=order.order_id)
        
    return render(request, 'store/checkout.html', {
        'items': items,
        'subtotal': subtotal,
        'buy_now': buy_now_item
    })

def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'store/order_success.html', {'order': order})

def generate_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.order_id}.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "GREENBUSKET")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Farm Fresh Organic Products")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 120, f"Invoice: {order.order_id}")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 140, f"Date: {order.created_at.strftime('%Y-%m-%d')}")
    c.drawString(50, height - 160, f"Customer: {order.customer_name}")
    c.drawString(50, height - 180, f"Phone: {order.phone}")
    c.drawString(50, height - 200, f"Address: {order.address}, {order.district}")
    
    y = height - 250
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Item")
    c.drawString(300, y, "Quantity")
    c.drawString(400, y, "Price")
    c.drawString(500, y, "Total")
    
    c.line(50, y - 5, 550, y - 5)
    
    y -= 25
    c.setFont("Helvetica", 12)
    for item in order.items.all():
        product_name = item.product.name if item.product else "Deleted Product"
        c.drawString(50, y, product_name[:35]) # limit length
        c.drawString(300, y, str(item.quantity))
        c.drawString(400, y, f"{item.price}")
        c.drawString(500, y, f"{item.price * item.quantity}")
        y -= 20
        
    c.line(50, y - 5, 550, y - 5)
    
    y -= 25
    c.drawString(400, y, "Delivery:")
    c.drawString(500, y, f"{order.delivery_charge}")
    
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y, "Total:")
    c.drawString(500, y, f"{order.total_amount}")
    
    c.save()
    return response
