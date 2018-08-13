import random, re, json



class Chain():
    def __init__(self):
        try:
            with open('markov.json', 'r') as f:
                self.json = json.load(f)
                self.freq = self.json['freq']
                self.roots = self.json['roots']
                self.status = True
        except IOError:
            self.json = {}
            self.freq = {}
            self.roots = []
            self.status = False

    def dump(self):
        self.json = {}
        self.json['freq'] = self.freq
        self.json['roots'] = self.roots
        try:
            with open('markov.json', 'w', newline='') as f:
                json.dump(self.json, f)
        except:
            try:
                with open('markov.json', 'w+', newline='') as f:
                    json.dump(self.json, f)
            except IOError as e:
                print("%s, exiting" % e)
                exit()

    def add_sentence(self, text, end):
        array = text.split()
        array.append(end)
        self.roots.append(array[0])
        while len(array) > 1:
            key = array[0]
            value = array[1]
            if not key == '' and not value == '':
                if key in self.freq:
                    self.freq[key].append(value)
                else:
                    self.freq[key] = [value]
            array.pop(0)


    def add_text(self, text):
        text = re.sub(r'\n\s*\n/m', '.', text).lower()
        seps = '([:;.?!,])'
        pieces = re.split(seps, text)[:-1]
        while len(pieces) > 1:
            content = pieces[0]
            if content[0] == ' ':
                content = content[1:]
            end = pieces[1]
            print(content, end)
            self.add_sentence(content, end)
            pieces.pop(0)
            pieces.pop(0)
        self.dump()

    def generate_sentence(self):
        res = ''
        seps = ':;.?!,'
        word = random.choice(self.roots)
        res += word
        run = True
        while run:
            word = random.choice(self.freq[word])
            if word in seps:
                res += word + ' '
                run = False
            else:
                res += ' ' + word
        return (res, word)

    def generate_text(self, length):
        res = ''
        hard_sep = '.?!'
        old = '.'
        while len(res) <= length:
            buf = self.generate_sentence()
            if len(res + buf[0]) + 2 < length:
                if old in hard_sep:
                    res += buf[0][0].upper() + buf[0][1:]
                else:
                    res += buf[0]
                old = buf[1]
            else:
                if not res[-2] in hard_sep:
                    end = res[-1]
                    while not end in hard_sep:
                        buf = self.generate_sentence()
                        if len(res + buf[0]) <= length + 10:
                            end = buf[1] 
                    res += buf[0]
                break
        return res[:-1]

if __name__ == "__main__":
    print("This won't work")
    exit()