from flask import Flask, render_template, request, redirect, send_file, session, flash
import os
import time
from werkzeug.utils import secure_filename
import cv2
from steagnography import LSBSteg

app = Flask(__name__)
app.secret_key = 'supersecretkey'
BASE_UPLOAD_FOLDER = 'storage'
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

def create_timestamped_folder():
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    folder_path = os.path.join(BASE_UPLOAD_FOLDER, timestamp)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == 'admin' and password == '1234':
        session['logged_in'] = True
        return redirect('/home')
    flash('Invalid Credentials')
    return redirect('/')

@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect('/')
    return render_template('index.html')

@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if not session.get('logged_in'):
        return redirect('/')
    if request.method == 'POST':
        upload_folder = create_timestamped_folder()
        image_file = request.files['image']
        text_file = request.files['text']

        img_path = os.path.join(upload_folder, secure_filename(image_file.filename))
        text_path = os.path.join(upload_folder, secure_filename(text_file.filename))
        image_file.save(img_path)
        text_file.save(text_path)

        image = cv2.imread(img_path)
        steg = LSBSteg(image)
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()

        encoded_image = steg.encode_text(text)
        output_path = os.path.join(upload_folder, 'encoded_output.png')
        cv2.imwrite(output_path, encoded_image)

        return send_file(output_path, as_attachment=True)
    return render_template('encode.html')

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if not session.get('logged_in'):
        return redirect('/')
    if request.method == 'POST':
        upload_folder = create_timestamped_folder()
        image_file = request.files['image']
        img_path = os.path.join(upload_folder, secure_filename(image_file.filename))
        image_file.save(img_path)

        image = cv2.imread(img_path)
        steg = LSBSteg(image)
        decoded_text = steg.decode_text()

        text_output_path = os.path.join(upload_folder, 'decoded_output.txt')
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write(decoded_text)

        return send_file(text_output_path, as_attachment=True)
    return render_template('decode.html')

if __name__ == '__main__':
    app.run(debug=True)