#Modules
from flask import Flask, render_template, flash, request, logging, redirect, url_for, session
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
from functools import wraps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import base64
def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))

def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')


app = Flask(__name__)

#MySQL configuration
mysql = MySQL(cursorclass=DictCursor)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'flaskappRT'
app.config['MYSQL_DATABASE_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql.init_app(app)

#Home
@app.route('/')
def home():
    return render_template('home.html', home=home)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Blogs
@app.route('/blogs')
@is_logged_in
def blogs():
    session['logged_in'] = True
    # Create cursor
    db = mysql.get_db()
    cur= db.cursor()
    # Get blogs
    result = cur.execute("SELECT * FROM blogs")
    blogs = cur.fetchall()
    if result > 0:
        return render_template('blogs.html', blogs = blogs)
    else:
        msg = 'No Blogs Found'
        return render_template('blogs.html', msg=msg)
    # Close connection
    cur.close()

#Events
@app.route('/events')
@is_logged_in
def events():
    session['logged_in'] = True
    # Create cursor
    db = mysql.get_db()
    cur= db.cursor()
    # Get blogs
    result = cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    if result > 0:
        flash('Due to maintainance, you are being redirected to the respective websites!', 'danger')
        return render_template('events.html', events = events)
    else:
        msg = 'No Events Found'
        return render_template('events.html', msg=msg)
    # Close connection
    cur.close()

#Blog
@app.route('/blog/<string:title>/')
@is_logged_in
def blog(title):
    session['logged_in'] = True
    # Create cursor
    db = mysql.get_db()
    cur= db.cursor()
    # Get blogs
    result = cur.execute("SELECT * FROM blogs WHERE title = %s", [title])
    blog = cur.fetchone()
    return render_template('blog.html', blog=blog)

#Register form class
class RegisterForm(Form):
    id = StringField('ID', [validators.length(min=1, max=15)])
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(),validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')
    college = StringField('College', [validators.length(min=5, max=100)])
    year = StringField('Present Year', [validators.length(min=1, max=5)])

#REGISTER
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        id = form.id.data
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = stringToBase64(form.password.data)
        college = form.college.data
        year = form.year.data
        try:
            #Create Cursor
            db = mysql.get_db()
            cur= db.cursor()
            # Execute query
            cur.execute("INSERT INTO users(id, name, username, email, password, college, year) VALUES(%s, %s, %s, %s, %s, %s, %s)", (id, name, username, email, password, college, year))
            print("executed!")
            #Commit to DB
            db.commit()
            # Close connection
        except Exception as e:
            print("EXCPE!: " + str(e))
            cur.close()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        id = request.form['id']
        password_candidate = request.form['password']
        # Create cursor
        db = mysql.get_db()
        cur= db.cursor()
        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE id = %s", [id])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = base64ToString(data['password'])
            # Compare Passwords
            if  password_candidate == password:
                # Passed
                session['logged_in'] = True
                session['id'] = id
                flash('You are now logged in', 'success')
                return redirect(url_for('home'))
            else:
                error = 'Invalid Password'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'ID not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Blogboard
@app.route('/blogboard')
@is_logged_in
def blogboard():
    session['logged_in'] = True
    # Create cursor
    db=mysql.get_db()
    cur=db.cursor()
    # Get blogs
    result = cur.execute("SELECT * FROM blogs")
    blogs = cur.fetchall()
    if result > 0:
        return render_template('blogboard.html', blogs=blogs)
    else:
        msg = 'No Blogs Found'
        return render_template('blogboard.html', msg=msg)
    # Close connection
    cur.close()

# Blog Form Class
class BlogForm(Form):
    title = StringField('Title', [validators.Length(min=1)])
    author = StringField('Author', [validators.Length(min=1)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Blog
@app.route('/addblog', methods=['GET', 'POST'])
@is_logged_in
def addblog():
    session['logged_in'] = True
    form = BlogForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        author = form.author.data
        users_id = session['id']
        # Create Cursor
        db=mysql.get_db()
        cur=db.cursor()
        # Execute
        cur.execute("INSERT INTO blogs(users_id, title, author, body) VALUES(%s, %s, %s, %s)",(users_id, title, author, body))
        # Commit to DB
        db.commit()
        #Close connection
        cur.close()
        flash('Blog Created', 'success')
        return redirect(url_for('blogboard'))
    return render_template('addblog.html', form=form)

# Edit Blog
@app.route('/editblog/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def editblog(id):
    # Create cursor
    db=mysql.get_db()
    cur=db.cursor()
    # Get blog by user
    users_id = session['id']
    if request.method == 'POST':
        try:
            print("Trying to update blog")
            title = request.form['title']
            body =request.form['body']
            # Create Cursor
            db=mysql.get_db()
            cur=db.cursor()
            app.logger.info(title)
            # Execute
            cur.execute("UPDATE blogs SET title=%s, body=%s  WHERE id=%s",(title, body, id))
            # Commit to DB
            db.commit()
            cur.close()
            flash('Blog Updated', 'success')
            return redirect(url_for('blogboard'))
        except Exception as e:
            print("EXCPE!: " + str(e))
            #Close connection
    result = cur.execute("SELECT * FROM blogs WHERE id = %s", id)
    blog = cur.fetchone()
    cur.close()
    # fill blog form fields
    form = BlogForm(request.form)
    form.title.data = blog['title']
    form.body.data = blog['body']
    return render_template('editblog.html', form=form)

# Delete Blog
@app.route('/delete_blog/<string:title>', methods=['POST'])
@is_logged_in
def delete_blog(title):
    session['logged_in'] = True
    # Create cursor
    db=mysql.get_db()
    cur=db.cursor()
    # Execute
    cur.execute("DELETE FROM blogs WHERE title = %s", [title])
    # Commit to DB
    db.commit()
    #Close connection
    cur.close()
    flash('Blog Deleted', 'success')
    return redirect(url_for('blogboard'))

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'danger')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug = True)
