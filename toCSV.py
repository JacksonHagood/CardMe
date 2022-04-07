import csv

def dict_to_csv(dictionary):

    
    filename = "dictionary_file.csv"
    with open (filename, "w", newline="") as csvfile:
        fields = ["keyword", "definition"]
        writer = csv.DictWriter(csvfile, delimiter=",", fieldnames=fields)
        writer.writeheader()
        #writer.writerow(dictionary[1])
        for key in dictionary:
            writer.writerow({fields[0]: key, fields[1]: dictionary[key]})
        #filename.close()
    #return 1