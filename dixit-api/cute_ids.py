import random

adjectives = ['fluffy', 'chonky', 'yellow', 'red', 'blue', 'shiny', 'light', 'bouncy', 'clever', 'ferocious', 'fiery',
              'frosty', 'electric', 'squishy', 'purple', 'majestic']
animals = ['bird', 'butterfly', 'ladybug', 'dolphin', 'kitten', 'puppy', 'rhino', 'bear', 'mouse', 'elephant',
           'squirrel', 'cheese', 'watermelon', 'feather']


def generate_cute_id():
    return "{}-{}".format(random.choice(adjectives), random.choice(animals))
