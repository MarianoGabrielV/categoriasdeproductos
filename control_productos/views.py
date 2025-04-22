
from django.shortcuts import render
from .models import Producto
from django.shortcuts import redirect
from .forms import ProductoForm
from django.shortcuts import get_object_or_404
from .models import Categoria, Producto
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria
from django.contrib.auth.decorators import login_required
from .models import Movimiento
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Count
from .models import Producto, Categoria, Movimiento
from django.db.models import Q
import openpyxl
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from django.http import HttpResponse



#def index(request):
#    productos = Producto.objects.all()
#    return render(request, 'control_productos/index.html', {'productos': productos})


#def agregar_producto(request):
#    if request.method == 'POST':
#       form = ProductoForm(request.POST)
#       if form.is_valid():
#            form.save()
#            return redirect('index')
#    else:
#        form = ProductoForm()
#    return render(request, 'control_productos/agregar_producto.html', {'form': form})



def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto_actualizado = form.save()
            return redirect('productos_por_categoria', categoria_id=producto_actualizado.categoria.id)
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'control_productos/editar_producto.html', {'form': form})



def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    categoria_id = producto.categoria.id  # guardamos antes de eliminar

    if request.method == 'POST':
        producto.delete()
        return redirect('productos_por_categoria', categoria_id=categoria_id)
    
    return render(request, 'control_productos/eliminar_producto.html', {'producto': producto})

def inicio(request):
    categorias = Categoria.objects.all()
    return render(request, 'control_productos/inicio.html', {'categorias': categorias})

def agregar_producto_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.categoria = categoria
            producto.save()
            return redirect('productos_por_categoria', categoria_id=categoria.id)
    else:
        form = ProductoForm()

    return render(request, 'control_productos/agregar_producto_categoria.html', {
        'form': form,
        'categoria': categoria
    })
@login_required
def productos_por_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    productos = Producto.objects.filter(categoria=categoria)

    # Filtros GET
    q = request.GET.get('q')
    tipo = request.GET.get('tipo')
    stock = request.GET.get('stock')

    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) |
            Q(precio__icontains=q)
        )

    if tipo == 'importado':
        productos = productos.filter(importado=True)
    elif tipo == 'nacional':
        productos = productos.filter(importado=False)

    if stock == 'sin':
        productos = productos.filter(stock=0)
    elif stock == 'bajo':
        productos = productos.filter(stock__lte=5, stock__gt=0)

    return render(request, 'control_productos/productos_por_categoria.html', {
        'categoria': categoria,
        'productos': productos
    })

def reponer_stock(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        try:
            cantidad = int(cantidad)
            if cantidad > 0:
                producto.stock += cantidad
                producto.save()

                # ✅ Registrar movimiento
                Movimiento.objects.create(
                    producto=producto,
                    usuario=request.user,
                    cantidad=cantidad,
                    tipo='reposicion'
                )

                messages.success(request, f'Se repusieron {cantidad} unidades de "{producto.nombre}".')
            else:
                messages.warning(request, 'La cantidad debe ser mayor a 0.')
        except ValueError:
            messages.error(request, 'Cantidad inválida.')

    return redirect('productos_por_categoria', categoria_id=producto.categoria.id)


def vender_stock(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        try:
            cantidad = int(cantidad)
            if cantidad > 0:
                if producto.stock >= cantidad:
                    producto.stock -= cantidad
                    producto.save()

                    # ✅ Registrar movimiento
                    Movimiento.objects.create(
                        producto=producto,
                        usuario=request.user,
                        cantidad=cantidad,
                        tipo='venta'
                    )

                    messages.success(request, f'Se vendieron {cantidad} unidades de "{producto.nombre}".')
                else:
                    messages.warning(request, f'Stock insuficiente. Disponible: {producto.stock}')
            else:
                messages.warning(request, 'La cantidad debe ser mayor a 0.')
        except ValueError:
            messages.error(request, 'Cantidad inválida.')

    return redirect('productos_por_categoria', categoria_id=producto.categoria.id)

@login_required
def exportar_productos_excel(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    productos = Producto.objects.filter(categoria=categoria)

    # Aplicar filtros si se usan
    tipo = request.GET.get('tipo')
    stock = request.GET.get('stock')

    if tipo == 'importado':
        productos = productos.filter(importado=True)
    elif tipo == 'nacional':
        productos = productos.filter(importado=False)

    if stock == 'sin':
        productos = productos.filter(stock=0)
    elif stock == 'bajo':
        productos = productos.filter(stock__lte=5, stock__gt=0)

    # Crear libro Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Productos - {categoria.nombre}"

    # Encabezados
    ws.append(["Nombre", "Precio", "Stock", "Tipo", "Categoría"])

    # Cargar productos
    for p in productos:
        ws.append([
            p.nombre,
            float(p.precio),
            p.stock,
            "Importado" if p.importado else "Nacional",
            p.categoria.nombre
        ])

    # Preparar respuesta
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename=productos_{categoria.nombre}.xlsx'
    wb.save(response)
    return response



@login_required
def exportar_productos_pdf(request, categoria_id):
    try:
        categoria = get_object_or_404(Categoria, pk=categoria_id)
        productos = Producto.objects.filter(categoria=categoria)

        tipo = request.GET.get('tipo')
        stock = request.GET.get('stock')

        if tipo == 'importado':
            productos = productos.filter(importado=True)
        elif tipo == 'nacional':
            productos = productos.filter(importado=False)

        if stock == 'sin':
            productos = productos.filter(stock=0)
        elif stock == 'bajo':
            productos = productos.filter(stock__lte=5, stock__gt=0)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=productos_{categoria.nombre}.pdf'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 50

        p.setFont("Helvetica-Bold", 16)
        p.drawString(40, y, f"Listado de Productos - {categoria.nombre}")
        y -= 20
        p.setFont("Helvetica", 10)
        p.drawString(40, y, f"Generado por: {request.user.username}")
        p.drawString(300, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 30

        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, "Nombre")
        p.drawString(200, y, "Precio")
        p.drawString(280, y, "Stock")
        p.drawString(350, y, "Tipo")
        y -= 15
        p.line(40, y, width - 40, y)
        y -= 20

        p.setFont("Helvetica", 10)
        for producto in productos:
            if y < 80:
                p.showPage()
                y = height - 50
            p.drawString(40, y, producto.nombre[:30])
            p.drawString(200, y, f"${producto.precio}")
            p.drawString(280, y, str(producto.stock))
            p.drawString(350, y, "Importado" if producto.importado else "Nacional")
            y -= 20

        p.showPage()
        p.save()
        return response

    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return HttpResponse("Error al generar el PDF.", status=500)