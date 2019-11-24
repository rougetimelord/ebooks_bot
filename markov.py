#markov.py, a markov chain manager
#Copyright (C) 2018 Blair "rouge" LaCriox
import random, re, json

class Chain():
    def __init__(self):
        """Reads the JSON or starts a new one.
        """

        try:
            with open('markov.json', 'r') as f:
                self.data = json.load(f)
                self.status = True
        except IOError:
            self.data = {}
            self.data['freq'] = {'\x02':[]}
            self.status = False

    def dump(self):
        """Dumps dictionary to JSON.
        """

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

    def add_sentence(self, text, end):
        """Adds a single sentence to the chain
        
        Arguments:
            text {str} -- The sentence to be added.
            end {str} -- The end of the sentence.
        """

        array = text.split()
        array.append(end)
        if array[0] == '\x03':
            return
        self.data['freq']['\x02'].append(array[0])
        while len(array) > 1:
            key = array[0]
            value = array[1]
            if key != '' and value != '':
                if key in self.data['freq']:
                    self.data['freq'][key].append(value)
                else:
                    self.data['freq'][key] = [value]
            array.pop(0)

    def add_text(self, text):
        """Adds text to the markov chain, by splitting it into sentences first.
        
        Arguments:
            text {str} -- The text to add
        """

        seps = '([\x02\x03])'
        pieces = re.split(seps, text)[:-1]
        while len(pieces) > 1:
            content = pieces[0]
            if len(content) != 0 and content[0] != ' ':
                end = pieces[1]
                self.add_sentence(content, end)
            pieces = pieces[2:]
        self.dump()

    def generate_sentence(self):
        """Generates a sentence of text.
    
        Returns:
            tuple -- A tuple with (String sentence, String ending_punctuation).
        """

        res = ''
        seps = '\x03'
        special = ',.?!'
        word = random.choice(self.data['freq']['\x02'])
        res += word
        run = True
        length = 1
        while run:
            try:
                word = random.choice(self.data['freq'][word])
            except KeyError as e:
                print('Choosing word failed with %s' % e)
                return ('', '')
            if word in seps:
                if length < 3:
                    res = word = random.choice(self.data['freq']['\x02'])
                    continue
                else:
                    run = False
                    break
            elif word in special:
                res += word + ' '
            else:
                res += ' ' + word
            length += 1
        return res

    def generate_text(self, length):
        """Generates text with length number of sentences.

        Arguments:
            length {int} -- How many sentences to make
        
        Returns:
            str -- The text generated.
        """

        res = ''

        for _ in range(length):
            res += self.generate_sentence()
            if length > 1:
                res += ' '

        return res
        

if __name__ == "__main__":
    print("This won't work")
    exit()