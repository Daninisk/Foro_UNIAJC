from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # password = db.Column(db.String(120), nullable=False) #Podrias omitir contraseña por ahora
    nombre_real = db.Column(db.String(120))  # nuevo campo para el nombre real
    registrado_en = db.Column(db.DateTime, default=datetime.utcnow)
    temas = db.relationship('Tema', backref='autor', lazy=True)
    mensajes = db.relationship('Mensaje', backref='autor', lazy=True)

    def __repr__(self):
        return f"<Usuario {self.username}>"

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    temas = db.relationship('Tema', backref='categoria', lazy=True)

    def __repr__(self):
        return f"<Categoria {self.nombre}>"

class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    mensajes = db.relationship('Mensaje', backref='tema', lazy=True)

    def __repr__(self):
        return f"<Tema {self.titulo}>"

class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False)

    def __repr__(self):
        return f"<Mensaje {self.id}>"


@app.route('/')
def inicio():
    categorias = Categoria.query.all()
    return render_template('index.html', categorias=categorias)

@app.route('/nueva_categoria', methods=['GET', 'POST'])
def nueva_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria_existente = Categoria.query.filter_by(nombre=nombre).first() #Verificar si existe
        if categoria_existente:
            #La categoria ya existe, mostrar un mensaje al usuario
            return render_template('nueva_categoria.html', error='Ya existe una categoría con ese nombre.') #Asegúrate de que este error se muestre en el template
        else:
            nueva_categoria = Categoria (nombre = nombre, descripcion = descripcion)
            db.session.add(nueva_categoria)
            db.session.commit()
            return redirect(url_for('inicio'))
    return render_template('nueva_categoria.html') #Asegúrate de que este template exista

@app.route('/categoria/<int:categoria_id>')
def mostrar_categoria(categoria_id):
    print("Se ha accedido a la función mostrar_categoria con ID: ", categoria_id)
    categoria = Categoria.query.get_or_404(categoria_id)
    temas = Tema.query.filter_by(categoria_id=categoria_id).all()
    print("Contenido de la variable 'temas' : ", temas)
    return render_template('categoria.html', categoria=categoria, temas=temas)

@app.route('/categoria/<int:categoria_id>/nuevo_tema', methods=['GET', 'POST'])
def nuevo_tema(categoria_id):
    print(f"¡La función nuevo_tema se ha llamado con categoria_id: {categoria_id}!")
    categoria = Categoria.query.get_or_404(categoria_id)
    if request.method == 'POST':
        autor_nombre = request.form['autor']
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        usuario = Usuario.query.filter_by(username=autor_nombre).first()
        if not usuario:
            usuario = Usuario(username=autor_nombre)
            db.session.add(usuario)
            db.session.commit()
        nuevo_tema = Tema(titulo=titulo, contenido=contenido, fecha_creacion=datetime.now(), autor=usuario, categoria=categoria) # MODIFICACIÓN AQUÍ
        db.session.add(nuevo_tema)
        db.session.commit()
        return redirect(url_for('mostrar_categoria', categoria_id=categoria_id))
    return render_template('nuevo_tema.html', categoria=categoria)

@app.route('/tema/<int:tema_id>')
def mostrar_tema(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    mensajes = Mensaje.query.filter_by(tema_id=tema_id).all()
    return render_template('tema.html', tema=tema, mensajes=mensajes)

@app.route('/tema/<int:tema_id>/nuevo_mensaje', methods=['POST'])
def nuevo_mensaje(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    autor_nombre = request.form['autor']
    contenido = request.form['contenido']

    usuario = Usuario.query.filter_by(username=autor_nombre).first()
    if not usuario:
        usuario = Usuario(username=autor_nombre)
        db.session.add(usuario)
        db.session.commit()

    nuevo_mensaje = Mensaje(contenido=contenido, fecha_creacion=datetime.now(), autor=usuario, tema=tema) # MODIFICACIÓN AQUÍ
    db.session.add(nuevo_mensaje)
    db.session.commit()

    return redirect(url_for('mostrar_tema', tema_id=tema_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Verificar si ya existen categorías
        if Categoria.query.count() == 0:
            # Si no existen, crea las categorías predefinidas para estudiantes
            categorias_iniciales = [
                {'nombre': 'Ventas entre Estudiantes', 'descripcion': 'Compra y venta de artículos de segunda mano entre estudiantes.'},
                {'nombre': 'Apoyo a Emprendimientos Estudiantiles', 'descripcion': 'Espacio para promocionar y apoyar pequeños negocios creados por estudiantes.'},
                {'nombre': 'Eventos y Actividades', 'descripcion': 'Información y discusión sobre eventos, talleres y actividades de interés para estudiantes.'},
                {'nombre': 'Ayuda y Tutorías', 'descripcion': 'Foro para solicitar o ofrecer ayuda académica y tutorías entre compañeros.'},
                {'nombre': 'Vida Universitaria', 'descripcion': 'Temas generales sobre la vida en la universidad, consejos, experiencias, etc.'}
                # Agrega aquí todas las categorías que desees
            ]
            for cat_data in categorias_iniciales:
                nueva_cat = Categoria(nombre=cat_data['nombre'],descripcion=cat_data['descripcion'])
                db.session.add(nueva_cat)
                db.session.commit()

app.run(host='0.0.0.0', port=3000, debug=True)
