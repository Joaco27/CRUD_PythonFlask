from flask import Flask
from flask import render_template, redirect, request, send_from_directory, flash, url_for
from flaskext.mysql import MySQL
import os
import datetime


actualUser = ''

app = Flask(__name__)
app.config['SECRET_KEY']='my secret key'
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST']='localhost'
app.config['MYSQL_DATABASE_USER']='root'
app.config['MYSQL_DATABASE_PASSWORD']=''
app.config['MYSQL_DATABASE_BD']='sistema'
mysql.init_app(app) 

CARPETA = os.path.join('uploads')
app.config['CARPETA'] = CARPETA

@app.route('/uploads/<nombreFoto>')
def uploads(nombreFoto):
    return send_from_directory(app.config['CARPETA'], nombreFoto)

@app.route('/')
def index():
    #sql1 = "INSERT INTO `sistema`.`empleados` (`id`, `nombre`, `correo`, `foto`)\
    #VALUES (NULL, 'Ana Maria', 'ana.maria@gmail.com', 'anamaria.jpg');"

    sql = "CREATE DATABASE IF NOT EXISTS menu;"
    
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS `menu`.`carta`(`id` INT(10) AUTO_INCREMENT PRIMARY KEY,`nombre` varchar(30),`foto` varchar(30),`costo` INT(10), `tipo` varchar(30));"
    cursor.execute(sql)
    
    sql = "CREATE DATABASE IF NOT EXISTS usuarios;"
    cursor.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS `usuarios`.`registrados`(`nombre` varchar(30) PRIMARY KEY,`password` varchar(30),`mail` varchar(30));"
    cursor.execute(sql)
    
    sql = "CREATE DATABASE IF NOT EXISTS compras;"
    cursor.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS `compras`.`ticket`(`producto` varchar(30), `costo` INT(10));"
    cursor.execute(sql)
    
    sql = "CREATE TABLE IF NOT EXISTS `compras`.`historial`(`usuario` varchar(30), `producto` varchar(30), `costo` INT(10), `fecha` varchar(30));"
    cursor.execute(sql)
    
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE tipo = 'entrada' ORDER BY costo")
    entries = cursor.fetchall()
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE tipo = 'principal' ORDER BY costo")
    main = cursor.fetchall()
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE tipo = 'bebida' ORDER BY costo")
    drinks = cursor.fetchall()
    conn.commit() 
    
    return render_template("menus/index.html", entradas=entries, principal=main, bebidas=drinks)

@app.route('/create')
def create():
    return render_template('menus/create.html')

@app.route('/store', methods=['POST'])
def storage():
    _nombre = request.form['txtNombre']
    _foto = request.files['txtFoto']
    _costo = request.form['txtCosto']
    _tipo = request.form['tipo']
    
    if "" in (_nombre, _costo):
        flash("Complete todos los campos")
        return render_template('menus/create.html')

    now = datetime.datetime.now()

    tiempo = now.strftime("%Y%H%M%S")

    if _foto.filename!='':
        nuevoNombreFoto=tiempo+_foto.filename
        _foto.save("uploads/"+nuevoNombreFoto)

    datos = (_nombre, nuevoNombreFoto, _costo, _tipo)

    sql = "INSERT INTO `menu`.`carta` \
          ( `nombre`, `foto`, `costo`, `tipo`) \
          VALUES (%s, %s, %s, %s);"
    conn = mysql.connect()     
    cursor = conn.cursor()     
    cursor.execute(sql, datos) 
    conn.commit()           
    return redirect('/')    

@app.route('/destroy/<int:id>')
def destroy(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM `menu`.`carta` WHERE id=%s", (id))
    conn.commit()
    return redirect('/')


@app.route('/edit/<int:id>')
def edit(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE id=%s", (id))
    menu=cursor.fetchall()
    conn.commit()
    return render_template('menus/edit.html', menu=menu)


@app.route('/update', methods=['POST'])
def update():
    _nombre = request.form['txtNombre']
    _foto = request.files['txtFoto']
    _costo = request.form['txtCosto']
    id = request.form['txtID']

    sql = "UPDATE `menu`.`carta` SET `nombre`=%s, `costo`=%s WHERE id=%s;"
    datos = (_nombre,_costo,id)

    conn = mysql.connect()
    cursor = conn.cursor()

    now = datetime.datetime.now()

    tiempo= now.strftime("%Y%H%M%S")

    if _foto.filename != '':
        nuevoNombreFoto = tiempo + _foto.filename
        _foto.save("uploads/" + nuevoNombreFoto)

        cursor.execute("SELECT foto FROM `menu`.`carta` WHERE id=%s", id)
        fila= cursor.fetchall()

        os.remove(os.path.join(app.config['CARPETA'], fila[0][0]))

        cursor.execute("UPDATE `menu`.`carta` SET foto=%s WHERE id=%s;", (nuevoNombreFoto, id))
        conn.commit()

    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/')

@app.route('/log')
def log():
    return render_template('menus/login.html')

@app.route('/login', methods = ['POST'])
def login():
    _name = request.form['txtNombre']
    user = request.form['txtNombre']
    _passw = request.form['txtPassword']
    if "" in (_name, _passw):
        flash("Complete todos los campos")
        return render_template('menus/login.html')
    
    global actualUser
    actualUser = user
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT * FROM `usuarios`.`registrados` WHERE (nombre = %s) and (password = %s)"
    datos = (_name, _passw)
    cursor.execute(sql,datos)
    resp = cursor.fetchall()
    if resp == ():
        flash("Nombre de usuario o contraseña incorrectos")
        return render_template('menus/login.html')
    conn.commit()
    return redirect('/')

@app.route('/register')
def register():
    return render_template('menus/register.html')

@app.route('/regist', methods = ['POST'])
def regist():
    _name = request.form['txtNombre']
    _passw = request.form['txtPassword']
    _mail = request.form['txtMail']
    if "" in (_name, _passw, _mail):
        flash("Complete todos los campos")
        return render_template('menus/register.html')
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `usuarios`.`registrados` WHERE (nombre = %s) OR (mail = %s)", (_name, _mail))
    resp = cursor.fetchall()
    if resp != ():
        flash("Nombre de usuario o mail ya registrados")
        return render_template('menus/register.html')
    datos = (_name, _passw, _mail)
    sql = "INSERT INTO `usuarios`.`registrados` \
          ( `nombre`, `password`, `mail`) \
          VALUES (%s, %s, %s);"
    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/')

@app.route('/shop')
def shop():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE tipo = 'entrada' ORDER BY costo")
    entries = cursor.fetchall()
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE tipo = 'principal' ORDER BY costo")
    main = cursor.fetchall()
    cursor.execute("SELECT * FROM `menu`.`carta` WHERE tipo = 'bebida' ORDER BY costo")
    drinks = cursor.fetchall()
    conn.commit() 
    
    return render_template("menus/shop.html", entradas=entries, principal=main, bebidas=drinks)


@app.route('/carrito')
def carrito():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `compras`.`ticket` WHERE 1 ORDER BY producto;")
    carrito = cursor.fetchall()
    cursor.execute("SELECT SUM(`costo`) FROM `compras`.`ticket` WHERE 1;")
    total = cursor.fetchall()
    conn.commit()
    return render_template('menus/carrito.html', carrito=carrito, total=total)

@app.route('/addCar/<prod>/<int:precio>')
def addCar(prod,precio):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO `compras`.`ticket` ( `producto`, `costo`)VALUES (%s, %s);",(prod, precio))
    conn.commit()
    return redirect('/shop')

@app.route('/destroyC/<prod>')
def destroyC(prod):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM `compras`.`ticket` WHERE producto=%s LIMIT 1", (prod))
    conn.commit()
    return redirect('/carrito')

@app.route('/users')
def users():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `usuarios`.`registrados` WHERE 1 ORDER BY nombre")
    resp = cursor.fetchall()
    conn.commit()
    return render_template('menus/users.html', users = resp)

@app.route('/destroyU/<nombre>')
def destroyU(nombre):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM `usuarios`.`registrados` WHERE nombre=%s", (nombre))
    conn.commit()
    return redirect('/users')

@app.route('/editU/<nombre>')
def editU(nombre):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `usuarios`.`registrados` WHERE nombre=%s", (nombre))
    users=cursor.fetchall()
    conn.commit()
    return render_template('menus/editU.html', users=users)

@app.route('/updateU', methods=['POST'])
def updateU():
    _nombre = request.form['txtNombre']
    _pasw = request.form['txtPassword']
    _mail = request.form['txtMail']

    # sql = "UPDATE `usuarios`.`registrados` SET `nombre`=%s, `password`=%s,  `mail`=%s WHERE nombre=%s;"
    sql = "UPDATE `usuarios`.`registrados` SET `password`=%s,  `mail`=%s WHERE nombre=%s;"
    datos = (_pasw,_mail,_nombre)

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/users')

@app.route('/buy')
def buy():
    global actualUser
    if actualUser == '':
        flash('Debe Iniciar Sesion Previamente')
        return redirect('/carrito')
    dateNow = datetime.datetime.now()
    dateNow = dateNow.strftime("%m/%d/%Y, %H:%M:%S")
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `compras`.`ticket` WHERE 1 ORDER BY producto;")
    ticket = cursor.fetchall()
    if ticket == ():
        flash('Debe Agregar Productos')
        return redirect('/carrito')
    cursor.execute("SELECT * FROM `compras`.`ticket` WHERE 1 ORDER BY producto;")
    ticket = cursor.fetchall()
    for t in ticket:
        cursor.execute("INSERT INTO `compras`.`historial` (`usuario`, `producto`, `costo`, `fecha`)VALUES (%s,%s,%s, %s);",(actualUser, t[0], t[1], dateNow))
    cursor.execute("DELETE FROM `compras`.`ticket` WHERE 1")
    conn.commit()
    return redirect('/')

@app.route('/history')
def history():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `compras`.`historial` WHERE 1")
    hist=cursor.fetchall()
    conn.commit()
    return render_template('menus/historial.html', hist=hist)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('menus/page_not_found.html'), 404



if __name__ == "__main__":
    app.run(debug=True)
