from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.producto import Producto
from app.models.pedido import Pedido
from app.models.lista_producto import ListaProducto
from app.models.venta import Venta
from app import db

# Se define el Blueprint 'pedidosinv_bp' que maneja la funcionalidad del administrador de pedidos
pedidosinv_bp = Blueprint('pedidosinv_bp', __name__)

# Función auxiliar para agregar la lista de productos asociados a cada pedido
def agregar_lista_productos(pedidos):
    """
    Asocia la lista de productos a cada pedido en la lista de pedidos proporcionada.
    
    Args:
        pedidos (list): Lista de instancias de Pedido.
    """
    for pedido in pedidos:
        lista_productos = ListaProducto.query.filter_by(codigo_pedido=pedido.codigo_ped).all()
        pedido.lista_productos = []
        for item in lista_productos:
            producto = Producto.query.get(item.codigo_producto)
            pedido.lista_productos.append({
                'producto_nombre': producto.nombre,
                'cantidad': item.cantidad
            })

# Ruta para mostrar la vista de administración de pedidos y productos
@pedidosinv_bp.route('/admin')
def admin():
    """
    Renderiza la vista de administración mostrando todos los productos y pedidos.
    
    Returns:
        render_template: Vista de administración con productos y pedidos.
    """
    productos = Producto.query.all()
    pedidos = Pedido.query.order_by(Pedido.estado.asc(), Pedido.codigo_ped.desc()).all()
    agregar_lista_productos(pedidos)  # Se agrega la lista de productos a los pedidos
    return render_template('admin.html', productos=productos, pedidos=pedidos)

# Ruta para buscar un pedido por su código
@pedidosinv_bp.route('/admin/buscar-pedido', methods=['GET'])
def buscar_pedido():
    """
    Permite buscar un pedido por su código y mostrar la vista de administración con los resultados.
    
    Returns:
        render_template: Vista de administración con los pedidos encontrados y productos.
    """
    codigo_ped = request.args.get('codigo_ped')  # Se obtiene el código de pedido de la URL
    pedidos = Pedido.query.filter_by(codigo_ped=codigo_ped).order_by(Pedido.estado.asc(), Pedido.codigo_ped.desc()).all()
    productos = Producto.query.all()
    agregar_lista_productos(pedidos)  # Se agrega la lista de productos a los pedidos encontrados
    return render_template('admin.html', productos=productos, pedidos=pedidos)

# Ruta para mostrar todos los pedidos
@pedidosinv_bp.route('/admin/mostrar-pedidos', methods=['GET'])
def mostrar_pedidos():
    """
    Muestra todos los pedidos en la vista de administración.
    
    Returns:
        render_template: Vista de administración con todos los pedidos y productos.
    """
    pedidos = Pedido.query.order_by(Pedido.estado.asc(), Pedido.codigo_ped.desc()).all()
    productos = Producto.query.all()
    agregar_lista_productos(pedidos)  # Se agrega la lista de productos a todos los pedidos
    return render_template('admin.html', productos=productos, pedidos=pedidos)

# Ruta para marcar un pedido como "recogido" y actualizar las existencias de los productos
@pedidosinv_bp.route('/admin/marcar-recogido/<int:codigo_ped>', methods=['POST'])
def marcar_recogido(codigo_ped):
    """
    Marca un pedido como recogido, registra la venta y actualiza las existencias de los productos.
    
    Args:
        codigo_ped (int): El código del pedido a marcar como recogido.
    
    Returns:
        redirect: Redirige a la vista de administración después de realizar la operación.
    """
    pedido = Pedido.query.get_or_404(codigo_ped)  # Obtiene el pedido por código o devuelve error 404
    
    # Verifica si el pedido ya ha sido marcado como recogido
    if pedido.estado:
        flash(f'El pedido {codigo_ped} ya está marcado como recogido', 'warning')
        return redirect(url_for('pedidosinv_bp.admin'))
    
    # Marca el pedido como recogido
    pedido.estado = True

    # Crea una nueva venta asociada a este pedido
    nueva_venta = Venta(codigo_pedido=codigo_ped)
    db.session.add(nueva_venta)

    # Actualiza las existencias de los productos en el pedido
    lista_productos = ListaProducto.query.filter_by(codigo_pedido=codigo_ped).all()
    for item in lista_productos:
        producto = Producto.query.get_or_404(item.codigo_producto)
        
        # Asegura que las existencias y cantidades sean enteros
        if isinstance(producto.existencias, str):
            producto.existencias = int(producto.existencias)
        if isinstance(item.cantidad, str):
            item.cantidad = int(item.cantidad)

        # Actualiza las existencias restando la cantidad vendida
        producto.existencias -= item.cantidad
        if producto.existencias < 0:
            flash(f'Error: El producto {producto.nombre} tiene existencias insuficientes.', 'danger')
            db.session.rollback()  # Si hay un error, hace rollback de la transacción
            return redirect(url_for('pedidosinv_bp.admin'))

    # Confirma los cambios en la base de datos
    try:
        db.session.commit()
        flash(f'Pedido {codigo_ped} marcado como recogido, venta registrada y existencias actualizadas', 'success')
    except Exception as e:
        db.session.rollback()  # Si ocurre un error, deshace la transacción
        flash(f'Error al marcar como recogido el pedido {codigo_ped}: {str(e)}', 'danger')
    
    return redirect(url_for('pedidosinv_bp.admin'))

# Ruta para eliminar un pedido
@pedidosinv_bp.route('/admin/eliminar-pedido', methods=['POST'])
def eliminar_pedido():
    """
    Elimina un pedido de la base de datos, así como los productos asociados a él.
    
    Returns:
        redirect: Redirige a la vista de administración después de eliminar el pedido.
    """
    codigo_ped = request.form.get('codigo_ped')  # Obtiene el código del pedido desde el formulario

    if not codigo_ped:
        flash('Código de pedido no proporcionado', 'danger')
        return redirect(url_for('pedidosinv_bp.admin'))

    pedido = Pedido.query.get(codigo_ped)  # Busca el pedido por su código
    if not pedido:
        flash('Pedido no encontrado', 'danger')
        return redirect(url_for('pedidosinv_bp.admin'))

    try:
        # Elimina los productos asociados al pedido
        ListaProducto.query.filter_by(codigo_pedido=codigo_ped).delete()
        # Elimina el pedido de la base de datos
        db.session.delete(pedido)
        db.session.commit()  # Realiza los cambios en la base de datos
        flash(f'Pedido {codigo_ped} eliminado correctamente', 'success')
    except Exception as e:
        db.session.rollback()  # Deshace la transacción en caso de error
        flash(f'Error al eliminar el pedido {codigo_ped}', 'danger')
    
    return redirect(url_for('pedidosinv_bp.admin'))
