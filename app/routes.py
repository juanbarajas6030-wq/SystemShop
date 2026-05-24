from app import app
from app.db import get_connection
from flask import render_template, request, redirect, url_for, session, flash

@app.route('/', methods=['GET'])
def index():

    busqueda = request.args.get('busqueda', '')

    conn = get_connection()
    cursor = conn.cursor

    if busqueda:

        query = """
            SELECT id, imagen, nombre, precioActual
            FROM sistemas
            WHERE nombre LIKE %s
        """

        cursor.execute(query, ('%' + busqueda + '%',))

    else:

        cursor.execute("""
            SELECT id, imagen, nombre, precioActual
            FROM sistemas
        """)

    productos = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(
        'index.html',
        productos=productos,
        busqueda=busqueda
    )

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/contactanos')
def contactanos():
    return render_template('contactanos.html')

@app.route('/agregar/<int:producto_id>')
def agregar_carrito(producto_id):
    conn = get_connection()
    cursor = conn.cursor

    cursor.execute("SELECT id, nombre, precioActual, imagen FROM sistemas WHERE id = %s", (producto_id,))
    producto = cursor.fetchone()

    cursor.close()
    conn.close()

    if not producto:
        return "Producto no encontrado", 404

    if 'carrito' not in session:
        session['carrito'] = []

    carrito = session['carrito']
    carrito.append(producto)
    session['carrito'] = carrito

    return redirect(url_for('index'))

@app.route('/eliminar/<int:indice>')
def eliminar_carrito(indice):

    if 'carrito' in session:

        carrito = session['carrito']

        if 0 <= indice < len(carrito):
            carrito.pop(indice)

        session['carrito'] = carrito

    return redirect(url_for('ver_carrito'))

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', [])
    total = sum(producto['precioActual'] for producto in carrito)
    return render_template('carrito.html', carrito=carrito, total=total)

@app.route('/hacer_pedido', methods=['POST'])
def hacer_pedido():
    if 'carrito' not in session or not session['carrito']:
        flash('El carrito está vacío', 'error')
        return redirect(url_for('ver_carrito'))
    
    if 'usuario' not in session:
        flash('Debes iniciar sesión para hacer un pedido', 'error')
        return redirect(url_for('logIn'))
    
    domicilio = request.form['domicilio']
    total = float(request.form['total'])
    usuario_id = session['usuario']['id']  # Asume que guardas el usuario en sesión al loguearse
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insertar cada producto del carrito como una instalación
        for producto in session['carrito']:
            cursor.execute("""
                INSERT INTO instalaciones (nombre, ubicacion, sistema_id, usuario_id, precio)
                VALUES (%s, %s, %s, %s, %s)
            """, (producto['nombre'], domicilio, producto['id'], usuario_id, producto['precioActual']))
        
        conn.commit()
        
        # Limpiar el carrito después de hacer el pedido
        session.pop('carrito', None)
        
        flash('Pedido realizado con éxito', 'success')
        return render_template('carrito_exitoso.html')  # Cambiado aquí
        
    except Exception as e:
        conn.rollback()
        print(f"Error al hacer pedido: {e}")
        flash('Error al procesar el pedido', 'error')
        return redirect(url_for('ver_carrito'))
        
    finally:
        cursor.close()
        conn.close()
        
@app.route('/logIn', methods=['GET', 'POST'])
def logIn():

    error = None

    if request.method == 'POST':

        email = request.form['email']
        contrasena = request.form['contrasena']

        conn = get_connection()
        cursor = conn.cursor

        query = """
            SELECT id, nombre
            FROM usuarios
            WHERE email = %s
            AND contrasena = %s
        """

        cursor.execute(query, (email, contrasena))

        usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        if usuario:

            session['usuario'] = usuario

            return redirect(url_for('index'))

        else:

            error = "Correo o contraseña incorrectos"

            return redirect(url_for('logIn'))

    return render_template('logIn.html', error=error)



@app.route('/singup', methods=['GET', 'POST'])
def singup():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contrasena = request.form['contrasena']
        
        # Obtener la conexión a la base de datos
        conn = get_connection()
        
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO usuarios (nombre, email, contrasena) VALUES (%s, %s, %s)"
            values = (nombre, email, contrasena)
            
            try:
                cursor.execute(query, values)
                conn.commit()
                print("Usuario registrado correctamente")
            except Exception as e:
                print(f"Error al insertar datos: {e}")
            finally:
                cursor.close()
                conn.close()
            return render_template('registro_exitoso.html')
    return render_template('singup.html')

@app.route('/logout')
def logout():

    session.pop('usuario', None)

    return redirect(url_for('logIn'))