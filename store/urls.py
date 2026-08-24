from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('tracking/', views.tracking, name='tracking'),
    
    path('cart/api/', views.cart_api, name='cart_api'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('order/success/<str:order_id>/', views.order_success, name='order_success'),
    path('order/invoice/<str:order_id>/', views.generate_invoice, name='generate_invoice'),
]
