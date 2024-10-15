import os
import mysql.connector
from flask import Flask, request, jsonify, render_template
from datetime import date
from cep import Transferencia

app = Flask(__name__)

# Función para conectar a la base de datos MySQL
def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="login_system"
    )

@app.route('/')
def form():
    return render_template('formulario.html')

@app.route('/validar-transferencia', methods=['POST'])
def validar_transferencia():
    tarjeta = request.form['tarjeta']
    criterio = request.form['criterio']
    emisor = request.form['emisor']
    monto = request.form['monto']
    correo = request.form['correo']  # Esto es el nombre_usuario
    banco = request.form['banco']

    # Convertir monto a float para manejar decimales
    try:
        monto_float = float(monto)
    except ValueError:
        return jsonify({'mensaje': 'El monto debe ser un número válido', 'estado': 'error'}), 400

    # Verificar que el monto sea mayor o igual a 100
    if monto_float < 100:
        return jsonify({'mensaje': 'NO SE PUEDE PROCESAR SU PAGO, RECUERDE QUE EL VALOR DEBE SER MAYOR O IGUAL A 100', 'estado': 'error'}), 400

    # Determinar el valor de la tarjeta y receptor
    if tarjeta == '2':
        tarjeta = '722969010354464015'
        receptort = '90722'
    elif tarjeta == '1':
        tarjeta = '127622001381033878'
        receptort = '40127'
    else:
        return jsonify({'error': 'Tarjeta no válida'}), 400
    
    fecha_actual = date.today()
    anio = fecha_actual.year
    mes = fecha_actual.month
    dia = fecha_actual.day

    # Conectar a la base de datos
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Verificar si el criterio ya ha sido utilizado en la tabla `autorecargas`
        cursor.execute("SELECT id FROM autorecargas WHERE criterio = %s", (criterio,))
        recarga_existe = cursor.fetchone()

        if recarga_existe:
            return jsonify({'mensaje': 'Esta transferencia ya ha sido procesada', 'estado': 'error'}), 400

        # Verificar si el usuario existe en la tabla `usuarios`
        cursor.execute("SELECT creditos FROM usuarios WHERE nombre_usuario = %s", (correo,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({'mensaje': 'Usuario no encontrado', 'estado': 'error'}), 404

        # Validar la transferencia
        tr = Transferencia.validar(
            fecha=date(anio, mes, dia),
            clave_rastreo=criterio,
            emisor=emisor,
            receptor=receptort,
            cuenta=tarjeta,
            monto=monto_float
        )

        if tr is None:
            return jsonify({'mensaje': 'Transferencia no encontrada', 'estado': 'error'}), 404

        # Actualizar los créditos del usuario
        print(f"Actualizando créditos para el usuario {correo} con un monto de {monto_float}")
        cursor.execute("UPDATE usuarios SET creditos = creditos + %s WHERE nombre_usuario = %s", (monto_float, correo))

        # Generar el nombre del archivo PDF con formato `fecha-criterio-correo.pdf`
        nombre_archivo_pdf = f"{fecha_actual}-{criterio}-{correo}.pdf"
        ruta_pdf = os.path.join("comprobantes", nombre_archivo_pdf)

        # Crear la carpeta 'comprobantes' si no existe
        if not os.path.exists("comprobantes"):
            os.makedirs("comprobantes")

        # Guardar el archivo PDF de la transferencia
        pdf_content = tr.descargar()
        with open(ruta_pdf, "wb") as f:
            f.write(pdf_content)

        # Guardar los detalles de la transferencia en `autorecargas` con el nombre del archivo PDF
        cursor.execute(
            "INSERT INTO autorecargas (criterio, correo, monto, fecha, estado, comprobante) VALUES (%s, %s, %s, %s, %s, %s)",
            (criterio, correo, monto_float, fecha_actual, 'exitoso', nombre_archivo_pdf)
        )

        # Confirmar los cambios
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'mensaje': 'ACTUALIZANDO CREDITOS'}), 200

    except mysql.connector.Error as e:
        # Si ocurre algún error, hacemos un rollback para evitar cambios parciales
        conn.rollback()
        print(f"Error al actualizar los créditos o insertar en autorecargas: {e}")
        return jsonify({'mensaje': f'Error al actualizar los créditos: {e}', 'estado': 'error'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
