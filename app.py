from flask import Flask, flash, render_template, request, redirect, jsonify, url_for, json
import pymysql # type: ignore
import secrets
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'static/assets/uploads'



def create_safe_filename(original_filename):
    # Santinize the original filename
    sanitized_filename= secure_filename(original_filename)

    # Extract the file extension
    _, ext = os.path.splitext(sanitized_filename)

    # Generate a UUID and create a new filename
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    return unique_filename


def upload(source_file):
    if source_file:
        safe_file_name = create_safe_filename(source_file.filename)
        try:
            source_file.save(os.path.join(app.config['UPLOAD_FOLDER'], safe_file_name))
        except Exception as e:
            return f"An error occurene {e}"
        else:
            return safe_file_name
    else:
        return "Source file error"
    




def get_database():
    try:
        return pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='FlaskEShop',
            ssl={'disable': True}
        )
    except pymysql.MySQLError as e:
        print(f"Error connecting to database: {e}")
        return None



def existing_data(tb, col, value):
    connection = get_database()
    cursor = connection.cursor()
    query = f"SELECT * FROM `{tb}` WHERE `{col}` = %s"
    cursor.execute(query, (value,))
    existing = cursor.fetchone()
    cursor.close()
    connection.close()
    return existing




# Front-end routes
@app.route('/')
def home():
    return render_template('frontend/home.html')

@app.route('/detail')
def detail():
    return render_template('frontend/detail.html')

@app.route('/shop')
def shop():
    return render_template('frontend/shop.html')

@app.route('/product')
def product():
    return render_template('frontend/product.html')

@app.route('/new')
def new():
    return render_template('frontend/new.html')

# Back-end routes
@app.route('/admin')
def admin():
    return render_template('admin/admin.html')

@app.route('/admin/list-product')
def listProduct():
    return render_template('admin/list-post.html')

@app.route('/admin/add-post', methods=["GET", "POST"])
def addPost():
    if request.method == 'GET':
        try:
            connection = get_database()
            cursor = connection.cursor()

            # Get Sizes
            cursor.execute("SELECT * FROM `attribute` WHERE `type`='size' ORDER BY `id` DESC")
            sizes = cursor.fetchall()

            # Get colors
            cursor.execute("SELECT * FROM `attribute` WHERE `type`='color' ORDER BY `id` DESC")
            colors = cursor.fetchall()

            # Get Category
            cursor.execute("SELECT * FROM `category` ORDER BY `id` DESC")
            categories = cursor.fetchall()

        except Exception as db_error:
            return jsonify({'message': str(db_error)})
        
        finally:
            connection.commit()
            connection.close()
            cursor.close()

        return render_template('admin/add-post.html', sizes=sizes, colors=colors, categories=categories)
    
    else:
        try:
            name = request.form['name']
            qty = int(request.form['qty'])
            regular_price = float(request.form['regular_price'])
            sale_price = float(request.form['sale_price'])
            sale_price = 0 if not sale_price else sale_price
            size          = request.form.getlist('size[]')
            color         = request.form.getlist('color[]')
            category_id   = int(request.form['category'])
            thumbnail     = request.files['thumbnail']
            description   = request.form['description']

            # upload image
            thumbnail = upload(thumbnail)

            # Join list size and color
            size = ','.join(size)
            color = ','.join(color)

            # Inset into database
            try:
                connection = get_database()
                cursor = connection.cursor()
                query = """
                            INSERT INTO `products` (`name`, `regularprice`, `available_size`, `category_id`, `quantity`, `sale_price`, `available_color`, `thumbnail`, `description`) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                cursor.execute(query, (name, regular_price, size, category_id, qty, sale_price, color, thumbnail, description,))
                connection.commit()
            
            except Exception as db_error:
                flash(message=str(db_error), category='danger')

            finally:
                cursor.close()
                connection.close()
                flash(message="Product added successfully", category='primary')

        except Exception as e:
            flash(message=str('plaese fill all field required!!'), category='danger')
        
    """ Response message """

    return redirect('/admin/add-post')


@app.route('/admin/list-products')
def list_products():
    try:
        connection = get_database()
        cursor = connection.cursor()

        cursor.execute(
            """
                SELECT `products`.*, `category`.name as category_name
                FROM `products`
                JOIN `category` ON `products`.category_id = category.id
            """
        )
        connection.commit()
        products = cursor.fetchall()

    except Exception as e:
        return jsonify({'error:': str(e)})
    finally:
        connection.close()
        cursor.close()
        keys = ["id", "name", "regular_price", "size", "category_id", "quantity", "sale_price", "color", "image", "description", "created_at", "category"]
        products_payload = [dict(zip(keys, product)) for product in products]

        # return jsonify(products_payload)

        return render_template('admin/list-products.html', products=products_payload)
    

# Admin add category
@app.route('/admin/add-category', methods=["GET", "POST"])
def addCategory():
    if request.method == 'POST':
        name = request.form['name']
        connection = get_database()

        if connection:
           
            
            if existing_data('category', 'name', name):
                message = f"{name} is already exists"
                status = "danger"
            else:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO `category` (`name`) VALUES (%s)", (name,))
                message = f"{name} added successfully!"
                status = 'success'

            # Terminate the connection
            connection.commit()  
            cursor.close()
            connection.close() 
                

            flash(message, status)
            return redirect(url_for('addCategory'))
        else:
            return "Database connection error", 500
        
    return render_template('admin/add-category.html')
# End admin add category



# Admin List Category
@app.route('/admin/list-categories')
def listCategories():
    connection = get_database()

    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM `category`")
        categories = cursor.fetchall()

        cursor.close()
        connection.close()
        # return jsonify(categories)
    
    return render_template('admin/list-category.html', categories=categories)
# end Admin List category



# Admin update category
@app.route('/admin/update-category/<id>', methods=["GET", "POST"])
def update_category(id):
    # connection = get_database()
    # cursor = connection.cursor()

    if request.method == "GET":
        connection = get_database()
        cursor = connection.cursor()
        if connection:
            try:
                cursor.execute("SELECT * FROM `category` WHERE `id` = %s", (id))
                category = cursor.fetchone()

                cursor.close()
                connection.close()

                return render_template('admin/update-category.html', category=category)
            except Exception as e:
                return jsonify({"error": str(e)})
    


    name = request.form['name']
    try:
        connection = get_database()
        cursor = connection.cursor()
        cursor.execute("UPDATE `category` SET `name`=%s WHERE `id`=%s", (name, id))
        connection.commit()

        cursor.close()
        connection.close()
        return redirect('/admin/list-categories')
    except Exception as e:
        return jsonify({"error": e})
    


# Admin delete Category
@app.route('/admin/delete-category', methods=["GET", "POST"])
def delete_category():
    if request.method == "POST":
        id = request.form['remove-id']
        # return id
        connection = get_database()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM `category` WHERE `id`=%s", (id))
        connection.commit()
        connection.close()
        cursor.close()
    return redirect('/admin/list-categories')



@app.route('/admin/add-attribute', methods=["GET", "POST"])
def add_attribute():

    if request.method == "GET":
        return render_template("admin/add-attribute.html")
    
    
    value = request.form['value']
    _type = request.form['type']
    # return jsonify([value, _type, _method])
    
    if existing_data(tb='attribute', col='value', value=value):
        message = f"{value} is already exists!"
        status = 'danger'
    else:
        # return jsonify({"error":"error"})
        try:
            connection = get_database()
            cursor = connection.cursor()
            # return jsonify({'data': [value, _type]})
            cursor.execute("INSERT INTO `attribute` (`value`, `type`) VALUES (%s, %s)", (value, _type))
        
            connection.commit()
            cursor.close()
            connection.close()
            message = f"{value} added successfully!"
            status = "success"
        except Exception as e:
            message = e
            status = 'danger'

    flash(message=message, category=status)
    return redirect('/admin/add-attribute')



@app.route('/admin/list-attribute')
def list_attribute():
    connection = get_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `attribute`")
    attributes = cursor.fetchall()
    connection.commit()
    connection.close()
    cursor.close()
    return render_template('admin/list-attribute.html', attributes=attributes)
    

@app.route('/admin/update-attribute/<id>', methods=["GET", "POST"])
def update_attribute(id):
    connection = get_database()
    cursor = connection.cursor()

    if request.method == "GET":
        cursor.execute("SELECT * FROM `attribute` WHERE `id` = %s", (id))
        attribute = cursor.fetchone()
        connection.commit()
        connection.close()
        cursor.close()
        return render_template('admin/update-attribute.html', attribute=attribute)
    
    value = request.form['value']
    _type = request.form['type']

    
    cursor.execute("UPDATE `attribute` SET `value`=%s, `type`=%s WHERE id = %s",(value, _type, id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash(message=f"{value} updated successfully!!", category="success")
    return redirect('/admin/list-attribute')



@app.route('/admin/delete-attribute', methods=["GET", "POST"])
def delete_attribute():
    id = request.form['remove-id']
    connection = get_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `attribute` WHERE `id` = %s", (id,))
    attribute = cursor.fetchone()
    cursor.execute("DELETE FROM `attribute` WHERE `id` = %s", (id,))
    connection.commit()
    cursor.close()
    connection.close()

    flash(message=f"{attribute[1]} deleted succeesfully", category="success")
    return redirect('/admin/list-attribute')

if __name__ == '__main__':
    app.run(debug=True)
