from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.proveedor import Proveedor
from app import db
from app.routes.rut import validar_rut  # Importar la función validar_rut
from app.routes.generador import generar_codigo_proveedor  # Importar la función de generación de código
from sqlalchemy.sql import text
from app.models import Proveedor, ListaProveedores

addproveedores_bp = Blueprint('addproveedores_bp', __name__)

@addproveedores_bp.route('/proveedores')
def registro():
    proveedores = Proveedor.query.all()
    return render_template('proveedores.html', proveedores=proveedores)

@addproveedores_bp.route('/registrar', methods=['POST'])
def addproveedores():
    if request.method == 'POST':
        rut_prov = request.form['rut_prov'].strip()
        razon_social = request.form['razon_social'].strip()
        correo = request.form['correo'].strip()
        telefono = request.form['telefono'].strip()
        direccion = request.form['direccion'].strip()
        representante = request.form['representante'].strip()

        # Validar el RUT
        if not validar_rut(rut_prov):
            flash('El RUT ingresado no es válido.', 'error')
            return render_template(
                'proveedores.html',
                rut_prov=rut_prov,
                razon_social=razon_social,
                correo=correo,
                telefono=telefono,
                direccion=direccion,
                representante=representante,
                proveedores=Proveedor.query.all()
            )

        # Verificar si el RUT ya está registrado
        proveedor_existente = Proveedor.query.filter_by(rut_prov=rut_prov).first()
        if proveedor_existente:
            flash('Este RUT ya ha sido registrado.', 'error')
            return redirect(url_for('addproveedores_bp.registro'))

        # Generar el código único de proveedor
        codigo_proveedor = generar_codigo_proveedor()

        nuevo_proveedor = Proveedor(
            rut_prov=rut_prov,
            razon_social=razon_social,
            correo=correo,
            telefono=telefono,
            direccion=direccion,
            representante=representante,
            codigo=codigo_proveedor  # Asignar el código generado
        )
        db.session.add(nuevo_proveedor)
        db.session.commit()
        flash('Proveedor añadido exitosamente.', 'success')
        return redirect(url_for('addproveedores_bp.registro'))


@addproveedores_bp.route('/modificar/<rut_prov>')
def get_proveedor(rut_prov):
    proveedor = Proveedor.query.filter_by(rut_prov=rut_prov).first()
    if not proveedor:
        flash('Proveedor no encontrado.', 'error')
        return redirect(url_for('addproveedores_bp.registro'))
    return render_template('modificar_proveedor.html', proveedor=proveedor)


@addproveedores_bp.route('/actualizar/<rut_prov>', methods=['POST'])
def actualizar_proveedor(rut_prov):
    if request.method == 'POST':
        # Obtener los datos actualizados desde el formulario
        razon_social = request.form['razon_social'].strip()
        correo = request.form['correo'].strip()
        telefono = request.form['telefono'].strip()
        direccion = request.form['direccion'].strip()
        representante = request.form['representante'].strip()

        # Buscar el proveedor por su RUT (que es la clave primaria)
        proveedor = Proveedor.query.filter_by(rut_prov=rut_prov).first()
        if not proveedor:
            flash('Proveedor no encontrado.', 'error')
            return redirect(url_for('addproveedores_bp.registro'))

        # Actualizar solo los campos permitidos
        proveedor.razon_social = razon_social
        proveedor.correo = correo
        proveedor.telefono = telefono
        proveedor.direccion = direccion
        proveedor.representante = representante

        # Guardar los cambios en la base de datos
        try:
            db.session.commit()
            flash('Proveedor actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el proveedor: {str(e)}', 'error')

        return redirect(url_for('addproveedores_bp.registro'))



@addproveedores_bp.route('/eliminar/<string:rut_prov>')
def eliminar_proveedor(rut_prov):
    # Buscar el proveedor por su RUT
    proveedor = Proveedor.query.filter_by(rut_prov=rut_prov).first()
    
    if proveedor:
        # Verificar si el RUT del proveedor está asociado a productos en la tabla lista_proveedores
        datos_asociados = ListaProveedores.query.filter_by(codigo_proveedor=rut_prov).count()

        if datos_asociados > 0:
            flash('No se puede eliminar el proveedor porque está asociado a productos.', 'error')
            return redirect(url_for('addproveedores_bp.registro'))

        # Proceder a eliminar el proveedor si no hay datos asociados
        try:
            db.session.delete(proveedor)
            db.session.commit()
            flash('Proveedor eliminado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar el proveedor: {str(e)}', 'error')
    else:
        flash('Proveedor no encontrado.', 'error')

    return redirect(url_for('addproveedores_bp.registro'))


