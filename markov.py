#markov.py, a markov chain manager
#Copyright (C) 2018 Blair "rouge" LaCriox
import random, re, json

class Chain():

    """Reads the JSON or starts a new one.
    """

    def __init__(self):
        #Open the json or create a new one
        try:
            with open('markov.json', 'r') as f:
                self.data = json.load(f)
                self.freq = self.data['freq']
                self.roots = self.data['roots']
                self.status = True
        except IOError:
            self.data = {}
            self.freq = {}
            self.roots = []
            self.status = False

    """Dumps dictionary to JSON.
    """

    def dump(self):
        self.data = {}
        self.data['freq'] = self.freq
        self.data['roots'] = self.roots
        try:
            with open('markov.json', 'w', newline='') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        except:
            try:
                with open('markov.json', 'w+', newline='') as f:
                    json.dump(self.data, f, indent=4, sort_keys=True)
            except IOError as e:
                print("%s, exiting" % e)
                exit()

    """Add a sentence by splitting it into words.
    """

    def add_sentence(self, text, end):
        array = text.split()
        array.append(end)
        if array[0] in ':;.?!,\n':
            return
        self.roots.append(array[0])
        while len(array) > 1:
            key = array[0]
            value = array[1]
            if key != '' and value != '':
                if key in self.freq:
                    self.freq[key].append(value)
                else:
                    self.freq[key] = [value]
            array.pop(0)

    """Adds text by splitting the text into sentences and adding the sentences.
    """

    def add_text(self, text):
        seps = '([:;.?!,\n])'
        pieces = re.split(seps, text)[:-1]
        while len(pieces) > 1:
            content = pieces[0]
            if len(content) != 0 and content[0] != ' ':
                end = pieces[1]
                self.add_sentence(content, end)
            pieces.pop(0)
            pieces.pop(0)
        self.dump()

    """Generates a sentence of text.
    
    Returns:
        Tuple -- A tuple with (String sentence, String ending_punctuation).
    """

    def generate_sentence(self):
        res = ''
        seps = ':;.?!,\n'
        try:
            word = random.choice(self.roots)
        except IndexError as e:
            print('Chosing a root failed with %s' % e)
            return ('', '')
        res += word
        run = True
        while run:
            try:
                word = random.choice(self.freq[word])
            except KeyError as e:
                print('Chosing word failed with %s' % e)
                return ('', '')
            if word in seps:
                if not word == "\n":
                    res += word + ' '
                run = False
                break
            elif not word in seps:
                res += ' ' + word
        return (res, word)

    """Generates a length of text
    
    Returns:
        String message -- The text for the tweet. 
    """

    def generate_text(self, length):
        res = ''
        hard_sep = '.?!\n'
        old = '.'
        while True:
            buf = self.generate_sentence()
            if len(res + buf[0]) < length + 10 and len(buf[0]) != 0:
                if old in hard_sep:
                    res += buf[0][0].upper() + buf[0][1:]
                else:
                    res += buf[0]
                old = buf[1]
            if len(res) < length + 10 and len(res) > length - 10:
                break
        return res[:-1]

if __name__ == "__main__":
    print("This won't work")
    exit()