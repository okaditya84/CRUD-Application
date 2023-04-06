from flask import Flask, jsonify, request, render_template, redirect , flash
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import os
from dotenv import load_dotenv
import re

load_dotenv()

# print(os.getenv("MONGO_URI")) # prints the value of the environment variable
URI=os.getenv("MONGO_URI")
# print(URI)

app = Flask(__name__, template_folder='templates', static_folder='static',static_url_path='/static')

# Configure secret key for flash messages

# Set up database connection
client = MongoClient(URI)
db = client["mydatabase"]
users_collection = db["users"]


# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users')
def get_all_users():

    users = users_collection.find()

    return render_template('users.html', users=users)

@app.route('/users/<user_id>')
def get_user(user_id):
    user = db.users.find_one({'_id': ObjectId(user_id)})
    return render_template('user.html', user=user)



@app.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        user_data = request.form.to_dict()
        email = user_data['email']
        password = user_data['password']
        
        
        
        # Check if the email is valid
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template('invalid_email.html')
        
        # Check if the email already exists in the database
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return render_template('email_exists.html')
        
        # Check password strength
        if len(password) < 8 or not any(char.isupper() for char in password) or not any(char in '!@#$%^&*()_-+={}[]|\:;"<>,.?/~`' for char in password):
            return render_template('weak_password.html')
        
        # Hash the password before storing it in the database
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data['password'] = hashed_password
        result = users_collection.insert_one(user_data)
        # Redirect back to create user page
        return redirect('/users/create')
    else:
        #pass the user_data dictionary to the template
        user_data={ 'name': '', 'email': '', 'password': ''}
        return render_template('create_user.html', user_data=user_data)


@app.route('/users/<user_id>/update', methods=['GET', 'POST'])
def update_user(user_id):
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if request.method == 'POST':
        user_data = request.form.to_dict()
        # Check if any required field is empty
        if any(field == '' for field in user_data.values()):
            return render_template('empty_fields.html', user=user)
        email = user_data['email']
        # Check if the email already exists in the database
        existing_user = users_collection.find_one({"email": email})
        if existing_user and existing_user['_id'] != ObjectId(user_id):
            return render_template('email_exists.html', user=user)
        # Check if the password meets the minimum length and complexity requirements
        password = user_data['password']
        if password:
            if len(password) < 8 or not any(char.isupper() for char in password) or not any(char in '!@#$%^&*()_-+=[{]}\|;:"<,>.?/' for char in password):
                return render_template('weak_password.html', user=user)
            # Hash the password before storing it in the database
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_data['password'] = hashed_password
        else:
            # If the password field is empty, do not update the password
            del user_data['password']
        # Check if the user data has changed
        if user_data == user:
            #print that the password is same as before
            return redirect('/users/' + str(user_id))
        result = users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": user_data})
        return redirect('/users/' + str(user_id))
    else:
        return render_template('update_user.html', user=user)


@app.route('/users/<user_id>/delete', methods=['GET', 'POST'])
def delete_user(user_id):
    if user_id:
        if request.method == 'POST':
            result = users_collection.delete_one({"_id": ObjectId(user_id)})
            return redirect('/users')
        else:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            return render_template('delete_user.html', user=user)
    else:
        return "User ID cannot be empty"


if __name__ == '__main__':
    app.run(debug=True)
