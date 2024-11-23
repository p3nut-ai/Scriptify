from flask import Flask, render_template, url_for, request, redirect, jsonify
import PyPDF2
from tts import tts, VOICES
import os
import shutil

app = Flask(__name__)

ALLOWED_EXTENSIONS = ['pdf']
UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# check if file is pdf, will return true or false
def if_pdf(filename):

    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
    print(f"File extension: {extension}")
    return extension in ALLOWED_EXTENSIONS

def move_audio_to_static(src_path, static_folder = app.config['UPLOAD_FOLDER']):
    try:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(static_folder, filename)

        normalized_dest_path = dest_path.replace(os.path.sep, '/')

        shutil.move(src_path, dest_path)

        return normalized_dest_path
    except Exception as e:
        print(f"[-] An error occurred while moving the file: {e}")
        return None

@app.route('/') # main route
def index():
    pdf_filename = request.args.get('pdf_filename')
    pdf_uploaded = request.args.get('pdf_uploaded')
    pathFile = request.args.get('pathFile')
    success_message = request.args.get('success_message')
    mp3_filename = request.args.get('mp3_filename')
    file_converted = request.args.get('file_converted')

    return render_template('main.html', pdf_filename = pdf_filename, pdf_uploaded = pdf_uploaded, pathFile = pathFile, voices = VOICES, success_message = success_message, mp3_filename = mp3_filename, file_converted = file_converted)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print(f"Received files: {request.files}")

        # Clean the upload folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Check if a file was uploaded
        if 'file' not in request.files:
            return redirect(url_for('index', success_message="No file uploaded."))

        file = request.files['file']
        filename = file.filename
        print(f"Uploaded file name: {filename}")

        # Validate file extension
        if file and if_pdf(filename):
            pathFile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(pathFile)
            return redirect(url_for('get_pdf', pathFile=pathFile, filename=filename, success_message=True))
        else:
            return redirect(url_for('index', success_message=False))

    return render_template('index.html')




@app.route('/get_pdf', methods=['GET', 'POST'])
def get_pdf():
    pdf_filename = request.args.get('filename')
    pathFile = request.args.get('pathFile')
    pdf_uploaded = True

    return redirect(url_for('index', pdf_filename = pdf_filename, pdf_uploaded = pdf_uploaded, pathFile = pathFile))


@app.route('/convert', methods=['POST'])
def convert_to_mp3():
    data = request.json
    voice = data.get('voice')
    filename = data.get('filename')

    if not voice or not filename:
        return jsonify({"error": "Invalid input"}), 400

    # Perform conversion logic here
    # For example, convert the file using a TTS library
    return jsonify({"message": "Conversion successful", "voice": voice, "filename": filename}), 200


@app.route('/convert_file', methods=['GET', 'POST'])
def convert_file():
    voice = request.form.get('voice')
    pdf_filename = request.form.get('file')
    pdf_path = request.form.get('pathFile')

    print(f"pdffilename = {pdf_filename}")
    print(f"pdffilename = {pdf_path}")
    print(f"voice = {voice}")

    txt_filename = pdf_path.rsplit(".", 1)[0] + ".txt"

    # print(txt_filename)

    txt_filename_edited = os.path.basename(txt_filename)

    # yung pdf file nag lalabas ng extra slash
    #  pdf_path == \\
    # Open the PDF file and read its content
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        with open(txt_filename, 'w') as text_file:
            for page in reader.pages:
                text = page.extract_text()
                if text:  # Check if text extraction was successful
                    text_file.write(text)

    return redirect(url_for('pass_txt', txt_filename = txt_filename, pdf_filename = pdf_filename, pdf_path = pdf_path, voice = voice))

@app.route('/pass_txt', methods=['GET', 'POST'])
def pass_txt():
    print("working with pass txt...")
    voice = request.args.get('voice')
    pdf_path = request.args.get('pdf_path')
    txt_path = request.args.get('pdf_path').rsplit('.', 1)[0] + '.txt'
    pdf_filename = request.args.get('pdf_filename')
    txt_filename = request.args.get('txt_filename')
    mp3_filename = pdf_path.rsplit('.', 1)[0] + '.mp3'
    print(f"File name received: {txt_filename}")

    displayOutput = txt_filename.rsplit('.', 1)[0] + '.mp3'


    mp3_filename = os.path.basename(mp3_filename)

    with open(txt_filename, 'r') as file:
        file_contents = file.read()

    os.remove(pdf_path)
    os.remove(txt_path)
    pdf_path = os.path.basename(pdf_path)
    txt_path = os.path.basename(txt_path)

    print(f"selected voice is {voice}")
    PDF_src_pathFile = os.path.join(app.config['UPLOAD_FOLDER'], mp3_filename)

    print(f"Path for PDF: {PDF_src_pathFile}")

    if voice:
        print(f'Voice selected: {voice}')
        tts(text=file_contents, voice = voice, filename = displayOutput, play_sound = False)

        return redirect(url_for('index', success_message = "Pdf conversion is successful", mp3_filename = mp3_filename, file_converted = True, pdf_filename = pdf_filename))  # Return a valid response
    else:
        return redirect(url_for('index', success_message = "No option was selected. Please select your voice."))

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # Check if it's a file and remove it
        # success_message = True
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f'Removed file: {file_path}')
    return redirect( url_for('index', success_message = True) )

if __name__ == '__main__':
    pass
