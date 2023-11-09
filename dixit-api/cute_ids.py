import random

adjectives = ['fluffy', 'chonky', 'yellow', 'red', 'blue', 'shiny', 'light', 'bouncy', 'clever', 'ferocious', 'fiery',
              'frosty', 'electric', 'squishy', 'purple', 'majestic', 'happy', 'sleepy', 'sunny', 'chocolate', 'green', 'orange']
animals = ['bird', 'butterfly', 'ladybug', 'dolphin', 'kitten', 'puppy', 'rhino', 'bear', 'mouse', 'elephant',
           'squirrel', 'cheese', 'watermelon', 'feather', 'bee', 'cat', 'dog', 'fish', 'frog', 'horse', 'lion', 'mushroom']



def generate_cute_id():
    return "{}-{}".format(random.choice(adjectives), random.choice(animals))
