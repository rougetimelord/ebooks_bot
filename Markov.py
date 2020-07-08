# markov.py, a markov chain manager
# Copyright (C) 2018 Blair "rouge" LaCriox
import random, re, json


class Chain:
    def __init__(self):
        """Reads the JSON or starts a new one.
        """

        try:
            with open("markov.json", "r") as f:
                self.data = json.load(f)
                self.status = True
        except IOError:
            self.data = {}
            self.data["freq"] = {"\x02": []}
            self.status = False

    def dump(self):
        """Dumps dictionary to JSON.
        """

        try:
            with open("markov.json", "w", newline="") as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        except:
            try:
                with open("markov.json", "w+", newline="") as f:
                    json.dump(self.data, f, indent=4, sort_keys=True)
            except IOError as e:
                print("%s, exiting" % e)
                exit()

    def add_sentence(self, text):
        """Adds a single sentence to the chain
        
        Arguments:
            text {str} -- The sentence to be added.
            end {str} -- The end of the sentence.
        """

        array = text.split()
        array.append("\x03")
        if array[0] == "\x03":
            return
        self.data["freq"]["\x02"].append(array[0])
        while len(array) > 1:
            key = array[0]
            value = array[1]
            if key != "" and value != "":
                if key in self.data["freq"]:
                    self.data["freq"][key].append(value)
                else:
                    self.data["freq"][key] = [value]
            array.pop(0)

    def add_text(self, text):
        """Adds text to the markov chain, by splitting it into sentences first.
        
        Arguments:
            text {str} -- The text to add
        """

        seps = "([\x02\x03])"
        pieces = re.split(seps, text)[:-1]
        while len(pieces) > 1:
            content = pieces[0]
            if len(content) != 0 and content[0] != " ":
                self.add_sentence(content)
            pieces = pieces[2:]
        self.dump()

    def generate_sentence(self):
        """Generates a sentence of text.
    
        Returns:
            str -- The sentence generated.
        """

        res = ""
        seps = "\x03"
        special = ",.?!:;"
        word = random.choice(self.data["freq"]["\x02"])
        res += word
        run = True
        while run:
            try:
                word = random.choice(self.data["freq"][word])
            except KeyError as e:
                print("Choosing word failed with %s" % e)
                return ("", "")
            if word in seps:
                run = False
                break
            elif word in special:
                res += word + " "
            else:
                res += " " + word
        return res

    def generate_text(self, length):
        """Generates text with length number of sentences.

        Arguments:
            length {int} -- How many sentences to make
        
        Returns:
            str -- The text generated.
        """

        res = ""

        for _ in range(length):
            res += self.generate_sentence()
            if length > 1:
                res += " "

        if len(res) > 280:
            return self.generate_text(length)
        else:
            return res


if __name__ == "__main__":
    print("This won't work")
    exit()
