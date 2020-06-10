# Gal Naor
# Gal's Trivia Game
# 10.06.2020
# Ver. 12

import socket
from tkinter import *
import threading
import time
import pickle
import sys


class GUI(Tk):
    def __init__(self, client):
        # self = Tk().
        super().__init__()
        self.client = client
        # Load assets
        self.gameLogo = PhotoImage(file="Assets\GameLogo.png")
        self.rightIcon = PhotoImage(file="Assets\Right.png")
        self.wrongIcon = PhotoImage(file="Assets\Wrong.png")
        self.x = 0
        self.y = 0
        self.radioVar = IntVar()

    def start(self):
        """ Main Function """
        self.protocol("WM_DELETE_WINDOW", self.closing)
        self.radioVar.set(-1)
        self.setWindow()
        self.client.connectToServer()
        self.openingScreen()

    def setWindow(self):
        """ Sets the window properties. """
        self.title("Gal's Trivia Game")
        self.geometry("%dx%d+%d+%d" % (800, 500, self.winfo_screenwidth() / 2 - 350, self.winfo_screenheight() / 2 - 300))
        self.config(background="#ffffff")
        self.resizable(0, 0)

    def openingScreen(self):
        """ Displays the opening screen. """
        labelImage = Label(
            self,
            image=self.gameLogo,
            background="#ffffff"
        )
        labelImage.pack()

        labelText = Label(
            self,
            text="Enter your name",
            font=("Arial Rounded MT Bold", 18),
            background="#ffffff"
        )
        labelText.pack(pady=(40, 10))

        nameEntry = Entry(
            self,
            font=("Arial Rounded MT Bold", 12),
            bd=3,
        )
        nameEntry.pack()
        nameEntry.bind("<Return>", lambda event: self.waitingScreen(nameEntry))
        nameEntry.focus_set()

        labelRules = Label(
            self,
            text="> >  Instructions  < <\n\nThe quiz contains 10 questions, each worth 5 points.\n"
                 "You'll have 10 seconds to solve each question.\nOnce you select an answer, "
                 "that will be the final choice.",
            width=100,
            font=("Arial Rounded MT Bold", 12),
            background="#ffffff",
        )
        labelRules.pack(pady=58)

    def waitingScreen(self, nameEntry):
        """ Entrance claim: Gets Entry widget.
         Exit claim: Gets the Entry's text and sends it to server. """
        name = nameEntry.get()
        if name == "":
            self.client.name = " "
        else:
            self.client.name = name
        self.client.sock.sendall("nnaame".encode())
        self.client.sock.sendall(self.client.name.encode())
        self.clearScreen()
        labelText = Label(
            self,
            text=". . .   wait for the quiz to start   . . .",
            font=("Arial Rounded MT Bold", 18),
            background="#ffffff",
        )
        labelText.pack(pady=210)
        t1 = threading.Thread(target=self.thread1)
        t1.daemon = True
        t1.start()

    def thread1(self):
        self.update_idletasks()
        self.update()
        self.startGame()

    def startGame(self):
        """ Process of the game. """
        while True:
            command, data = self.client.getQuestion()
            if command != " ":
                print(command)
                print(data)
                if command == "show all players":
                    print("here")
                    self.showAllPlayers(data)
                else:
                    self.showQuestion(data)
                command = None
            while True:
                try:
                    self.update_idletasks()
                    self.update()
                except TclError:
                    if self.y == 1:
                        sys.exit()
                    pass

    def showQuestion(self, data):
        """ Entrance claim: Gets tuple of question & answers.
        Exit claim: Displays it on screen. """
        self.clearScreen()
        labelTimer = Label(
            self,
            text="",
            font=("Arial Rounded MT Bold", 28),
            foreground="#bcfebf",
            background="#ffffff"
        )
        labelTimer.pack(pady=20)

        labelNumOfQues = Label(
            self,
            text="-   Question " + str(data[0]) + "   -",
            font=("Arial Rounded MT Bold", 17),
            background="#ffffff"
        )
        labelNumOfQues.pack()

        labelQuestion = Label(
            self,
            text=data[1],
            justify=LEFT,
            font=("Arial Rounded MT Bold", 14),
            background="#ffffff",
        )
        labelQuestion.pack(pady=(20, 20))

        r1 = Radiobutton(
            self,
            text=data[2],
            font=("Arial Rounded MT Bold", 13),
            value=1,
            variable=self.radioVar,
            command=lambda: self.answerQuestion(r1, r2, r3, r4),
            background="#ffffff",
        )
        r1.pack(pady=5)

        r2 = Radiobutton(
            self,
            text=data[3],
            font=("Arial Rounded MT Bold", 13),
            value=2,
            variable=self.radioVar,
            command=lambda: self.answerQuestion(r1, r2, r3, r4),
            background="#ffffff",
        )
        r2.pack(pady=5)

        r3 = Radiobutton(
            self,
            text=data[4],
            font=("Arial Rounded MT Bold", 13),
            value=3,
            variable=self.radioVar,
            command=lambda: self.answerQuestion(r1, r2, r3, r4),
            background="#ffffff",
        )
        r3.pack(pady=5)

        r4 = Radiobutton(
            self,
            text=data[5],
            font=("Arial Rounded MT Bold", 13),
            value=4,
            variable=self.radioVar,
            command=lambda: self.answerQuestion(r1, r2, r3, r4),
            background="#ffffff",
        )
        r4.pack(pady=5)

        timerHandler = threading.Thread(target=self.countdownTimer, args=(labelTimer,))
        timerHandler.daemon = True
        timerHandler.start()

    def answerQuestion(self, r1, r2, r3, r4):
        """ Entrance claim: Gets four radio buttons.
        Exit claim: Sets answer as the button's number, makes all buttons disabled. """
        answer = self.radioVar.get()
        if answer == 1:
            r1['selectcolor'] = "#000000"
            r2['state'] = 'disabled'
            r3['state'] = 'disabled'
            r4['state'] = 'disabled'
        if answer == 2:
            r2['selectcolor'] = "#000000"
            r1['state'] = 'disabled'
            r3['state'] = 'disabled'
            r4['state'] = 'disabled'
        if answer == 3:
            r3['selectcolor'] = "#000000"
            r1['state'] = 'disabled'
            r2['state'] = 'disabled'
            r4['state'] = 'disabled'
        if answer == 4:
            r4['selectcolor'] = "#000000"
            r1['state'] = 'disabled'
            r2['state'] = 'disabled'
            r3['state'] = 'disabled'
        self.radioVar.set(-1)
        self.client.answer = answer

    def countdownTimer(self, labelTimer):
        """ Entrance claim: Gets label which shows the remaining seconds.
        Exit claim: Updates the seconds, sends answer to server. """
        for i in range(3):
            try:
                labelTimer['text'] = str(3 - i)
                print(3 - i)
                time.sleep(1)
            except:
                pass
        try:
            self.client.sock.sendall(str(self.client.answer).encode())
            self.client.answer = 5
            self.showRW(self.client.getRW())
        except:
            pass

    def showRW(self, rw):
        """ Entrance claim: Gets right / wrong.
        Exit claim: Displays it on screen."""
        self.clearScreen()
        labelImage = Label(
            self,
            image=self.rightIcon,
            background="#ffffff"
        )
        if rw == "wrong":
            labelImage['image'] = self.wrongIcon
        labelImage.pack(pady=(50, 0))

        labelText = Label(
            self,
            text="score | " + str(self.client.score),
            font=("Arial Rounded MT Bold", 15),
            background="#ffffff",
        )
        labelText.pack(pady=50)
        self.startGame()

    def showAllPlayers(self, listClients):
        """ Entrance claim: Gets names & scores list.
        Exit claim: Displays it on screen. """
        print("im in ShowAllPlayers")
        self.clearScreen()
        labelText = Label(
            self,
            text="T H A N K S   F O R   P L A Y I N G",
            font=("Arial Rounded MT Bold", 18),
            background="#ffffff",
        )
        labelText.pack(pady=(30, 40))

        labelScores = Label(
            self,
            text="S C O R E S\n\n",
            font=("Arial Rounded MT Bold", 12),
            background="#ffffff",
        )
        labelScores.pack()

        labelTable = Label(
            self,
            justify=LEFT,
            text="",
            font=("Arial Rounded MT Bold", 12),
            background="#ffffff",
        )
        labelTable.pack()
        i = 1
        for Client in listClients:
            labelTable['text'] += str(i) + ". Name: " + str(Client[0]) + "   |   Score: " + str(Client[1]) + "\n\n"
            i += 1

        labelImage = Label(
            image=self.gameLogo,
            background="#ffffff"
        )
        labelImage.pack(side=BOTTOM)
        try:
            self.update_idletasks()
            self.update()
        except:
            print("No update.")

    def clearScreen(self):
        """ Clears the screen. """
        for child in self.winfo_children():
            child.destroy()

    def closing(self):
        print("closing")
        self.y = 1
        try:
            self.client.sock.sendall("ccllosing".encode())
        except:
            pass
        self.client.sock.close()
        self.destroy()


# -


class Client(object):
    def __init__(self, serverIP,  serverPort):
        self.ip = serverIP
        self.port = serverPort
        self.sock = None
        self.name = ""
        self.score = 0
        self.answer = 5

    def connectToServer(self):
        """ Creates Client Socket & Connects to Server Socket. """
        print('%s | %s' % (self.ip, self.port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        print('connected to server.')
        msg = self.sock.recv(1024)
        print('SERVER: %s' % msg.decode())

    def getQuestion(self):
        """ Receives data (question / players & scores list) from Server & returns it. """
        try:
            data = self.sock.recv(1024)
            try:
                if data.decode() == "players and scores":
                    data = self.sock.recv(1024)
                    time.sleep(0.2)
                    data = pickle.loads(data)
                    return "show all players", data
            except:
                data = pickle.loads(data)
                return "show question", data
        except:
            return " ", ("0", "1")

    def getRW(self):
        """ Receives from server whether the answer is right / wrong & returns it."""
        rw = self.sock.recv(1024).decode()
        if rw == "right":
            self.score += 5
        return rw


# - - - - -


def main():
    client = Client('127.0.0.1', 4000)
    Game = GUI(client)
    Game.start()
    Game.mainloop()


if __name__ == '__main__':
    main()
