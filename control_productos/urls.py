
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('categoria/<int:categoria_id>/', views.productos_por_categoria, name='productos_por_categoria'),
    path('categoria/<int:categoria_id>/agregar/', views.agregar_producto_categoria, name='agregar_producto_categoria'),
    path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('reponer/<int:producto_id>/', views.reponer_stock, name='reponer_stock'),
    path('vender/<int:producto_id>/', views.vender_stock, name='vender_stock'),
    path('categoria/<int:categoria_id>/exportar-excel/', views.exportar_productos_excel, name='exportar_excel'),
    path('categoria/<int:categoria_id>/exportar-pdf/', views.exportar_productos_pdf, name='exportar_pdf'),
     path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),


    


]





