import random
import copy

reset_data = {
    None: {
        'count': 1,
        'outputs': {
            '67': 1
        }
    },
    '67': {
        'count': 1,
        'outputs': {
            None: 1
        }
    }
}

words_data = {
    None: {
        'count': 1,
        'outputs': {
            '67': 1
        }
    },
    '67': {
        'count': 1,
        'outputs': {
            None: 1
        }
    }
}

def feed(string):
    if string == "": return
    words = string.split(" ")
    for i, word in enumerate([None] + words):
        next_word = None if i == len(words) else words[i]
        if word in words_data:
            words_data[word]['count'] += 1
            outputs: dict = words_data[word]['outputs']
            if next_word in outputs:
                outputs[next_word] += 1
            else:
                outputs[next_word] = 1
        else:
            words_data[word] = {
                'count': 1,
                'outputs': {
                    next_word: 1
                }
            }

def chain(word):
    index = random.randrange(words_data[word]['count'])
    outputs = words_data[word]['outputs']
    count = 0
    for word, weight in outputs.items():
        count += weight
        if count > index:
            return word

def gen_response():
    word = None
    output = ""
    while True:
        word = chain(word)
        if not word: return output
        output += (" " if output != "" else "") + word

def clear_response():
    global words_data
    words_data = copy.deepcopy(reset_data)