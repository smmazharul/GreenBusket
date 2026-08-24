from django.contrib import admin
from .models import Category, Product, ProductVariant, Order, OrderItem

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]
    list_editable = ('price', 'stock', 'is_active')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer_name', 'phone', 'district', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'district', 'created_at')
    search_fields = ('order_id', 'customer_name', 'phone')
    inlines = [OrderItemInline]
    readonly_fields = ('order_id', 'total_amount', 'delivery_charge')
    list_editable = ('status',)
