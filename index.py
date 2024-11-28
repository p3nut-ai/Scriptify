from flask import Flask, render_template, url_for, request, redirect, jsonify, make_response
from termcolor import colored
import PyPDF2
from tts import tts, VOICES
import os
import shutil
import fitz
print(f"HELLO WORLD {fitz.__doc__}")
app = Flask(__name__)

ALLOWED_EXTENSIONS = ['pdf']
MAX_PAGES = 12
uploads_directory = os.path.join(os.getcwd(), "static", "uploads")

# will check if the extension is pdf or not, will return TRUE OR FALSE
def allowed_extension(filename):
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
    print(f"File extension: {extension}")
    return extension in ALLOWED_EXTENSIONS

# will move the output file from main directory to static/uploads
def move_audio_to_static(src_path, static_folder = uploads_directory):
    try:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(static_folder, filename)

        normalized_dest_path = dest_path.replace(os.path.sep, '/')

        shutil.move(src_path, dest_path)

        return normalized_dest_path
    except Exception as e:
        print(f"[-] An error occurred while moving the file: {e}")
        return None

def remove_images_from_pdf(input_pdf_path, output_pdf_path):
    # Open the PDF
    doc = fitz.open(input_pdf_path)

    # Iterate through all the pages
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Get all images on the page
        image_list = page.get_images(full=True)

        # If there are images, we will remove them
        for image_index, img in enumerate(image_list):
            xref = img[0]  # The xref is the reference to the image object

            # Remove the image by deleting the image reference
            page.delete_image(xref)

        # After removing images, we can proceed to the next page (no need to handle text)

    # Save the new PDF without images
    doc.save(output_pdf_path, incremental=True)

    print(f"PDF saved without images: {output_pdf_path}")


def clean_upload_folder():
    for filename in os.listdir(uploads_directory):
            file_path = os.path.join(uploads_directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    print(colored(f"Upload folder is now clean!"))

def is_pdf(file):
    header = file.read(4)
    file.seek(0)
    return header == b'%PDF'

@app.route('/') # main route
def index():
    pdf_filename = request.args.get('pdf_filename')
    pdf_uploaded = request.args.get('pdf_uploaded')
    pathFile = request.args.get('pathFile')
    success_message = request.args.get('success_message')
    mp3_filename = request.args.get('mp3_filename')
    file_converted = request.args.get('file_converted')
    limit_exceed = request.args.get('limit_exceed')
    num_pages = request.args.get('num_pages')
    reader = request.args.get('reader')

    return render_template('main.html', reader = reader, limit_exceed = limit_exceed, num_pages = num_pages, MAX_PAGES = MAX_PAGES, pdf_filename = pdf_filename, pdf_uploaded = pdf_uploaded, pathFile = pathFile, voices = VOICES, success_message = success_message, mp3_filename = mp3_filename, file_converted = file_converted)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print(f"Received files: {request.files}")

        # Clean the upload folder
        clean_upload_folder()

        # Check if a file was uploaded
        if 'file' not in request.files:
            return redirect(url_for('index', success_message = False))

        file = request.files['file']
        filename = file.filename

        ifPDF = is_pdf(file)

        if not ifPDF:
            return redirect(url_for('index', success_message = False))

        print(colored("FILE UPLOADED", "green"))
        print(colored(f"UPLOADED FILE NAME : {filename}", "yellow"))

        # Validate file extension
        if file and allowed_extension(filename):
            file.save(filename)
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)

            # Check if the number of pages exceeds the limit
            if num_pages > MAX_PAGES:
                print("file exceed 10 pages")
                move_audio_to_static(filename)
                # Redirect to the index page if it exceeds the limit
                return redirect(url_for('index', limit_exceed = True, num_pages = num_pages, MAX_PAGES = MAX_PAGES, reader = reader))

            return redirect(url_for('get_pdf', filename = filename, reader = reader, success_message = True))
        else:
            return redirect(url_for('index', success_message = False))

    return render_template('index.html')

@app.route('/get_pdf', methods=['GET', 'POST'])
def get_pdf():
    pdf_filename = request.args.get('filename')
    pdf_uploaded = True

    return redirect(url_for('index', pdf_filename = pdf_filename, pdf_uploaded = pdf_uploaded))

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
    reader = reader = request.form.get('reader')
    txt_filename = pdf_filename.rsplit(".", 1)[0] + ".txt"

    # remove_images_from_pdf(pdf_filename, pdf_filename)

    with open(pdf_filename, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        with open(txt_filename, 'w') as text_file:
                for page in reader.pages:
                    text = page.extract_text()
                    if text:  # Check if text extraction was successful
                        text_file.write(text)

    print(colored(f"VOICE : {voice}", "yellow"))
    print(colored(f"PDF NAME : {pdf_filename}", "yellow"))
    print(colored(f"TXT PATH : {txt_filename}", "yellow"))

    return redirect(url_for('pass_txt', txt_filename = txt_filename, pdf_filename = pdf_filename, voice = voice))

@app.route('/pass_txt', methods=['GET', 'POST'])
def pass_txt():
    print(colored(f"PASSING THE TXT FILE TO TTS FUNCTION...", "green"))

    voice = request.args.get('voice')
    pdf_filename = request.args.get('pdf_filename')
    txt_filename = request.args.get('txt_filename')
    mp3_filename = txt_filename.rsplit('.', 1)[0] + '.mp3'

    print(colored(f"SELECTED VOICE : {voice}", "yellow"))
    print(colored(f"PDF NAME : {pdf_filename}", "yellow"))
    print(f"Checking file: {txt_filename}")

    # Ensure file exists
    if not os.path.isfile(txt_filename):
        print(colored(f"Error: File does not exist: {txt_filename}", "red"))
        return jsonify({"error": f"File not found: {txt_filename}"}), 404

    # Open file safely
    try:
        with open(txt_filename, 'r') as file:
            file_contents = file.read()
    except Exception as e:
        print(colored(f"Error reading file: {e}", "red"))
        return jsonify({"error": "Could not read file"}), 500

    move_audio_to_static(pdf_filename)
    move_audio_to_static(txt_filename)

    if voice:
        print(colored(f"VOICE SELECTED : {voice}", "cyan"))

        tts(text=file_contents, voice=voice, filename=mp3_filename, play_sound=False)

        move_audio_to_static(mp3_filename)

        return redirect(url_for('index', success_message=True, mp3_filename=mp3_filename, file_converted=True, pdf_filename=pdf_filename))
    else:
        return redirect(url_for('index', success_message=False))

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    clean_upload_folder()
    return redirect(url_for('index', success_message = True))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
