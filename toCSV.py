# imports
from flask import Flask, render_template, request, redirect, jsonify, make_response
import csv
import os, io

def dict_to_csv(dictionary):
    address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr)
    print(os.path.dirname(__file__) + "\\static\\csv\\" + address)
    os.makedirs(os.path.dirname(__file__) + "\\static\\csv\\" + address)
    
    filename = os.path.dirname(__file__) + "\\static\\csv\\" + address + "\\dictionary_file.csv"
    with open (filename, "w", newline="") as csvfile:
        fields = ["keyword", "definition"]
        writer = csv.DictWriter(csvfile, delimiter=",", fieldnames=fields)
        writer.writeheader()
        #writer.writerow(dictionary[1])
        for key in dictionary:
            writer.writerow({fields[0]: key, fields[1]: dictionary[key]})
        #filename.close()
    #return 1