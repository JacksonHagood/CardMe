def getDefinitions(text: str):

    # first symbol seperates words with their definitions
    first = "$"
    # second symbol seperates one word,definiton pair from another
    # appears at the end of each definition
    second = "#"

    current = 0
    start = 0

    # return dictionary 
    ret = dict()

    while(current < len(text)):

        if ((text[current] == second) and (current + 2 > len(text) or text[current+1] == "\n" or text[current+2] == "\n")):
            word_def = text[start:current]

            # find the split index
            word_index = word_def.find(first)

            if word_index < 0: # if seperator not found, use " " as seperator
                word_index = word_def.find(" ")
            if word_index < 0: # illegal data
                print("COULD NOT PARSE: ", word_def)
                current += 1
                continue

            our_word = word_def[:word_index].strip().strip("\n")
            our_definition = word_def[word_index+1:].strip().strip("\n")

            ret[our_word] = our_definition

            # update start of next word
            start = current + 1

        current += 1

    return ret