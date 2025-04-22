from django.contrib import admin
from .models import Producto, Categoria
from .models import Movimiento

admin.site.register(Movimiento)
admin.site.register(Producto)
admin.site.register(Categoria)
