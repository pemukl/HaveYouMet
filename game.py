from collections import defaultdict
from os import listdir
from random import sample, choice, choices
from pandas import DataFrame

defaultpath = "famous/"

class Game:
    games = {}
    players = {}
    config = {}

    def __new__(cls, config):
        if config["picturePath"] in Game.games:
            return Game.games[config["picturePath"]]
        else:
            return super(Game, cls).__new__(cls)

    def __init__(self, config):
        if config["picturePath"] not in Game.games:
            self.path = config["picturePath"]
            self.players = {}
            self.imgs = self.load_imgs()
            Game.games[self.path] = self

    def load_imgs(self):
        imgs = {}
        for file in listdir(self.path + "images/"):
            if file.endswith(".jpeg"):# and len(file) < 19:
                imgs[file] = Image(self.path + "images/" + file)
        print(f"found {len(imgs)} images")
        return imgs

    def get_player(self, id):
        if id not in self.players:
            self.players[id] = Player(self, id)
        return self.players[id]


class Image:
    def __init__(self, path):
        filename = path.split("/")[-1]
        self.filename = filename
        trimmed = filename.split(".")[0]
        trimmed = [x.capitalize() for x in trimmed.split("-")]
        self.name = " ".join(trimmed)
        self.wrongs = 0
        self.rights = 0
        self.confusions = defaultdict(int)

    def guess(self, guess):
        if guess.name == self.name:
            self.rights += 1
            return True
        else:
            self.wrongs += 1
            self.confusions[guess.filename] += 1
            return False


class Player:
    def __init__(self, game, playerId):  # init method
        print("New Player: " + str(playerId))
        self.game = game
        self.playerId = playerId
        self.correct = 0
        self.wrong = 0
        self.weights = {key: 8 for key in self.game.imgs.keys()}

    def __str__(self):
        return str(self.playerId)

    def score(self):
        return self.correct - self.wrong

    def generate_challenge(self):
        image_path = choices(list(self.weights.keys()), weights=list(self.weights.values()))[0]
        image = self.game.imgs[image_path]
        imgs = list(self.game.imgs.values())
        alternatives = []
        for i in range(3):
            weights = []
            for img in imgs:
                if img == image or img in alternatives:
                    weights.append(0)
                else:
                    weights.append(1 + image.confusions[img.filename])

            alternatives.append(choices(imgs, weights=weights)[0])
        alt_weigts = [1 + image.confusions[alt.filename] for alt in alternatives]
        print(f"New W{self.weights[image.filename]} for {self.playerId}: {image.name} vs. {[(alt.name, alt_weigts[i]) for i, alt in enumerate(alternatives)]}")
        correct = choice(range(4))
        options = alternatives[:correct] + [image] + alternatives[correct:]
        return Challenge(options, correct, self)


class Challenge:
    image = None
    options = None
    correct = None
    player = None
    picked = None

    def __init__(self, options, correct, player):  # init method
        image = options[correct]
        self.image = image
        self.options = options
        self.correct = correct
        self.player = player
        self.picked = [0, 0, 0, 0]

    def get_image_path(self):
        return self.player.game.path + "images/" + self.image.filename

    def get_options(self):
        return [option.name for option in self.options]

    def pick_option(self, choosen):
        self.image.guess(self.options[choosen])
        if choosen == self.correct:
            print("Correct!")
            self.picked[choosen] = 1
            self.player.correct += 1
            self.player.weights[self.image.filename] /=2
            return True
        else:
            print("Wrong: " + self.options[choosen].name)
            self.picked[choosen] = -1
            self.player.wrong += 1
            self.player.weights[self.image.filename] *= 2
            return False

    def __str__(self):
        return f"Challenge: {self.image} {self.options} {self.correct}"
