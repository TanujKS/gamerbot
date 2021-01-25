def convertListtoStr(list : list):
    answer = ""
    for l in list:
        answer += l
    return answer

def displayGame():
    zipLists = zip(Column1.columnList, Column2.columnList, Column3.columnList, Column4.columnList, Column5.columnList, Column6.columnList, Column7.columnList)
    res = "\n".join("{} {} {} {} {} {} {}".format(a, b, c, d, e, f, g) for a, b, c, d, e, f, g in zipLists)
    print(res)

class Column():
    def __init__(self):
        self.column = "⚫⚫⚫⚫⚫⚫"
        self.columnList = list(self.column)
    def put(self, emoji):
        index = 0
        for c in self.columnList:
            if self.columnList[index] != "⚫":
                self.columnList[index - 1] = emoji
                self.column = convertListtoStr(self.columnList)
                return
            if index == len(self.columnList) - 1:
                self.columnList[index] = emoji
                self.column = convertListtoStr(self.columnList)
                return
            index += 1

class Player():
    def __init__(self, emoji, name):
        self.emoji = emoji
        self.name = name


for i in range(1, 8):
    globals()[f"Column{i}"] = Column()

Player1 = Player("🔴", "Tanuj")
Player2 = Player("🔵", "Arman")
players = [Player1, Player2]


game = True
while game:
    for player in players:
        move = input(f"{player.name}s turn: ")
        globals()[f"Column{move}"].put(player.emoji)
        displayGame()
