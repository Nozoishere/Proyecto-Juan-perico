from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.cliente import Cliente
from app.routes.rut import validar_rut  # Importar la función validar_rut

registro_bp = Blueprint('registro_bp', __name__)

@registro_bp.route('/registro')
def registroclie():
    return render_template('registro.html')

@registro_bp.route('/registrarclie', methods=['POST'])
def registrarclie():
    if request.method == 'POST':
        rut_clie = request.form['rut_clie']
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        direccion = request.form['direccion']
        edad = request.form['edad']

        # Validar el RUT
        if not validar_rut(rut_clie):
            return jsonify({'status': 'error', 'title': 'Error', 'message': 'El RUT ingresado no es válido'})

        # Verificar si el rut_clie ya está registrado
        cliente = Cliente.query.filter_by(rut_clie=rut_clie).first()
        if cliente:
            return jsonify({'status': 'error', 'title': 'Error', 'message': 'El RUT ya está registrado'})

        # Verificar si el correo ya está registrado
        cliente_correo = Cliente.query.filter_by(correo=correo).first()
        if cliente_correo:
            return jsonify({'status': 'error', 'title': 'Error', 'message': 'El correo electrónico ya está registrado'})

        # Verificar si la edad es negativa
        if int(edad) < 0:
            return jsonify({'status': 'error', 'title': 'Error', 'message': 'La edad no puede ser negativa'})

        # Crear nuevo cliente
        nuevo_cliente = Cliente(
            rut_clie=rut_clie,
            nombre=nombre,
            correo=correo,
            contrasena=contrasena,
            direccion=direccion,
            edad=edad
        )
        db.session.add(nuevo_cliente)
        db.session.commit()

        # Mensaje de éxito
        return jsonify({'status': 'success', 'title': 'Éxito', 'message': 'Registrado exitosamente'})
