# imports
import convertapi
from Crypto.PublicKey import RSA
from flask import Flask, render_template, request, redirect, jsonify, make_response, send_from_directory, send_file
from googleapiclient.discovery import build
from google.cloud import vision_v1
from google.cloud.vision_v1 import types
from werkzeug.utils import secure_filename
import json
import os, io
import pandas
import pyrebase
import re

# databse configuration (credentials removed for public GitHub)
config = {}

# initialize databse
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# initialize youtube api (credentials removed for public GitHub)
ytKey1 = ""
ytKey2 = ""
ytKey3 = ""
ytKey4 = ""
ytKey5 = ""
ytKey6 = ""
ytKey7 = ""

# allow for multiple YouTube keys
ytKeyList = [ytKey1, ytKey2, ytKey3, ytKey4, ytKey5, ytKey6, ytKey7]
youtube = [build("youtube", "v3", developerKey = youtubeApiKey) for youtubeApiKey in ytKeyList]

# global folder name
folderName = None

# flask app
app = Flask(__name__)

# page handler
@app.route("/<name>")
def index(name):
    if name == "index":
        # index page
        return render_template("index.html")
    elif name == "folders":
        # folders page
        return render_template("folders.html", data = folders())
    elif name == "flashcards":
        # flashcards page
        return render_template("flashcards.html", data = [["word1", "def1", "a"], ["word2", "def2", "b"]])
    elif name == "uploadimage":
        # flashcards page
        return render_template("upload_image.html")
    else:
        # page not found
        return render_template("index.html")

# error 404 handler
@app.errorhandler(404)
def handle_404(e):
    # index.html as default
    return render_template("index.html")

# image directory (update when on Heroku)
path = os.path.join(app.root_path, "static", "img", "uploads")
app.config["IMAGE_UPLOADS"] = path

# function for allowed images
def allowed_image(filename):
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]: 
        return True
    else:
        return False

# helper function for extracting dictionary of flashcards from string
def getDefinitions(text: str):
    # first symbol seperates words with their definitions
    first = "*"

    # second symbol seperates one word,definiton pair from another
    second = "#"

    current = 0
    start = 0
    ret = dict()

    while(current < len(text)):

        if ((text[current] == second) and (current + 2 > len(text) or text[current+1] == "\n" or text[current+2] == "\n")):
            word_def = text[start:current]

            # find the split index
            word_index = word_def.find(first)

            if word_index < 0: # if seperator not found, use " " as seperator
                word_index = word_def.find(" ")
            if word_index < 0: # illegal data
                current += 1
                continue

            our_word = word_def[:word_index].strip().strip("\n").replace("\n", " ")
            our_definition = word_def[word_index+1:].strip().strip("\n").replace("\n", " ")

            ret[our_word] = our_definition

            # update start of next word
            start = current + 1

        current += 1

    return ret

# control what type of image can be accepted
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG", "PDF"]

# handler for uploading an image
@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():
    # image posting handler
    if request.method == "POST":

        if request.files:
            # save image
            image = request.files["image"]
            
            # checks for illegal file types
            if image.filename == "":
                return render_template("upload_image.html")

            # save image
            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))

            else:
                return redirect(request.url)

            # start API request (credentials removed for public GitHub)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = None
            client = vision_v1.ImageAnnotatorClient()

            # get file path
            FILE_PATH = os.path.join(path, image.filename)

            # read image
            with io.open(FILE_PATH, 'rb') as image_file:
                content = image_file.read()

            # issue request and take response
            image = vision_v1.types.Image(content = content)
            response = client.document_text_detection(image = image)

            # accept text gathered from image
            image_text = response.full_text_annotation.text

            # use parser to get dictionary of flashcards
            res = getDefinitions(image_text)

            # get folder name from text entry
            folder_name = request.form["text"]

            # get IP address, remove periods
            address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]

            # create directory with IP address, folder name, and (update) flashcards
            db.child(address).child(folder_name).update(res)

    # refresh page
    return render_template("upload_image.html")
@app.route("/runFlashcards", methods=['POST'])
def runFlashcards():
    global folderName
    folderName = request.form['item_fn']
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]
    folderObject = db.child(address).child(folderName).get()

    # stores data to pass into flashcards page
    data = []

    for pair in folderObject.each():
        youtubeIndex = 0 # index of api Key
        youtubeLink = "https://youtube.com" # default link in case api breaks

        # find the working api key and use that
        while(youtubeIndex < len(youtube)): 
            try:
                youtubeRequest = youtube[youtubeIndex].search().list(
                    part="snippet",
                    maxResults=1,
                    q=pair.key(),
                    type="video"
                )
                youtubeResponse = youtubeRequest.execute()
                youtubeLink = "https://youtube.com/watch?v=" + youtubeResponse["items"][0]["id"]["videoId"]
                break
            except:
                youtubeIndex += 1
                continue

        temp = [pair.key(), pair.val(), youtubeLink]
        data.append(temp)

    return render_template("flashcards.html", data = data, fold_n = folderName)

# when user clicks edit 
@app.route("/editFlashcards", methods=['POST'])
def editFlashcards():
    folderName = request.form['item_fn']
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]
    folderObject = db.child(address).child(folderName).get()

    data = []

    for pair in folderObject.each():
        data.append([pair.key(), pair.val()])

    return render_template("editing.html", data = data, fName=folderName)

# button to export PDF
@app.route("/flashcards", methods=["POST"])
def flashcards():
    global folderName
    temp = request.data

    # get IP address, remove periods
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]

    print("X:", address)

    # get items from folder
    items = db.child(address).child(folderName).get()

    print("Y:", address)

    # create dictionary from items
    Dictionary = dict()

    for item in items.each():
        Dictionary.update({item.key(): item.val()})
    
    # convert dictionary to list of tuples
    Tuples = [(term, definition) for term, definition in Dictionary.items()]

    # create array of flashcard items
    cards = []

    # indexer
    i = 0

    # add 2 pages at a time, alternate between terms and definition
    for i in range(2, len(Tuples), 3):
        cards.append(Tuples[i - 2][0])
        cards.append(Tuples[i - 1][0])
        cards.append(Tuples[i][0])
        cards.append(Tuples[i - 2][1])
        cards.append(Tuples[i - 1][1])
        cards.append(Tuples[i][1])

    # leftovers 1
    if i < len(Tuples) - 2:
        cards.append(Tuples[i + 1][0])
        cards.append(Tuples[i + 2][0])
        cards.append("[spacer]")
        cards.append(Tuples[i + 1][1])
        cards.append(Tuples[i + 2][1])
        cards.append("[spacer]")

    # leftovers 2
    elif i < len(Tuples) - 1:
        cards.append(Tuples[i + 1][0])
        cards.append("[spacer]")
        cards.append("[spacer]")
        cards.append(Tuples[i + 1][1])
        cards.append("[spacer]")
        cards.append("[spacer]")
    
    # html start
    text = '<html><body>'

    # add divs for each item in cards
    for card in cards:
        text += '<div style = "margin: auto; margin-top: 25px; margin-bottom: 25px; font-size: 50px; text-align: center; width: 75%; height: 500px; border: 5px solid black"><p style = "padding: 150px 0px;">' + card + '</p></div>'

    # html end
    text += '</body></html>'

    # write to html file
    file = open("out.html", "w")
    file.write(text)
    file.close()

    # invoke API (credentials removed for public GitHub)
    convertapi.api_secret = ""
    convertapi.convert("pdf", {
        "File": "out.html"
    }, from_format = "html").save_files("out.pdf")

    # delete html file
    os.remove("out.html")

    # return PDF
    return send_from_directory("", "out.pdf")

# handler for my folders page (to display the folders)
@app.route("/folders", methods=["GET", "POST"])
def folders():
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]
    print(db)
    print(address)
    foldernames = db.child(address).get()
    print(foldernames)
    fn_list = []
    for fn in foldernames.each():
        fn_list.append(fn.key())

    #return render_template("folder names: ")
    return render_template("folders.html", mylist = fn_list)

# when user confirms all changes
@app.route("/<folderName>/comfirmEdit", methods=['POST'])
def confirmEdit(folderName):
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]

    res = {}
    index = 0

    for key_ in request.form.keys():
        if key_[0] == "w":
            currentWord = request.form.get(key_)
            currentDef = request.form.get(f"def-{key_[-1]}")
            res[currentWord] = currentDef

    db.child(address).child(folderName).remove() # clear the folder
    db.child(address).child(folderName).update(res) # add new data

    return runFlashcards() # return user to flashcards page

# demo button to export PDF
@app.route("/deleteFolder", methods=["POST"])
def deleteFolder():
    global folderName

    # get IP address, remove periods
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr).replace('.', "")[0:3]

    # get items from folder
    db.child(address).child(folderName).remove()

    return folders()
