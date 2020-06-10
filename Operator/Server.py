# Gal Naor
# Gal's Trivia Game
# 10.06.2020
# Ver. 12

import socket
import threading
import sqlite3
import time
import pickle
import sys


class Server(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.count = 0                         # number of clients
        self.listClients = []                  # list contains: [clientSocket, id]
        self.connQ = None
        self.connP = sqlite3.connect("players.db", check_same_thread=False)
        # check_same_thread = False: used for updating database inside a thread (which isn't a main-thread).
        self.row = None
        self.y = 0

    def start(self):
        """ Main Function """
        try:
            self.players_db()
            # Create Server Socket
            print('%s | %s' % (self.ip, self.port))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((self.ip, self.port))
            # Choose topic
            topic = input("> Choose a topic ( python / israel ): ")
            while True:
                topic = topic.strip().lower()
                if topic == "python":
                    self.connQ = sqlite3.connect("questionsPY.db")
                    self.questionsPY_db()
                    break
                if topic == "israel":
                    self.connQ = sqlite3.connect("questionsIS.db")
                    self.questionsIS_db()
                    break
                topic = input("> Try again: ")
            # Choose number of participants
            num = input("> Choose number of participants: ")
            while True:
                try:
                    num = int(num)
                    if num == 0:
                        num = input("> Try again: ")
                    else:
                        break
                except:
                    num = input("> Try again: ")
            sock.listen(num)
            x = 1
            insertparm = """INSERT INTO players(id, name, score) VALUES(?, ?, ?);"""
            while True:
                # Wait for clients & Start a thread to each client connected
                print('waiting for clients...')
                (clientSocket, clientAddress) = sock.accept()
                print('new client entered.')
                clientSocket.sendall('Wellcome to Gal\'s Trivia Game!'.encode('utf8'))
                self.listClients.append([clientSocket, x])
                self.connP.execute(insertparm, (x, " ", 0))
                self.count += 1
                clientHandler = threading.Thread(target=self.handleClients, args=(clientSocket, x))
                clientHandler.daemon = True
                clientHandler.start()
                x += 1
                if self.count == num:
                    print("\n> > >   START OF QUIZ   < < <\n")
                    break
            while self.y != self.count:
                pass

            input("\n> Press ENTER to start: ____")
            if topic == "python":
                cursor = self.connQ.execute("SELECT * from questionsPY")
            else:
                cursor = self.connQ.execute("SELECT * from questionsIS")
            rows = cursor.fetchall()
            for row in rows:
                self.row = row
                self.sendQuestion(self.listClients)
                print("- start 10 seconds -")
                time.sleep(3)
                print("- end 10 seconds -")
                input("\n> Press ENTER to continue: ____")
            print("\n> > >   END OF QUIZ   < < <\n")
            self.sendAllClients()
            for Client in self.listClients:
                Client[0].close()
            sock.close()
            self.connQ.close()
            self.connP.execute("SELECT * from players")
            self.connP.close()

        except socket.error:
            print(socket.error)

    def handleClients(self, clientSocket, x):
        """ Entrance claim: Client socket, id.
         Exit claim: Receive answer from client & Send to him right (+ update score) or wrong"""

        selectparm = """SELECT score from players where id=?"""
        replaceparm1 = """UPDATE players set score=? where id=?;"""
        replaceparm2 = """UPDATE players set name=? where id=?;"""
        while True:
            try:
                answer = clientSocket.recv(1024)
                answer = answer.decode()
                if answer == "ccllosing":
                    self.closing(clientSocket, x)
                if answer == "nnaame":
                    name = clientSocket.recv(1024)
                    name = name.decode()
                    print(name)
                    self.connP.execute(replaceparm2, (name, x,))
                    self.y += 1
                else:
                    if answer == str(self.row[-1]):
                        rw = "right"
                        scorecol = self.connP.execute(selectparm, (x,))
                        for s in scorecol:
                            sco = s[0] + 5
                            self.connP.execute(replaceparm1, (sco, x,))
                            break
                    else:
                        rw = "wrong"
                    clientSocket.sendall(rw.encode())
            except:
                pass

    def sendQuestion(self, listClients):
        """ Entrance claim: Gets list of clients sockets.
        Exit claim: Sends the current question to all clients. """
        data = pickle.dumps(self.row)
        for Client in listClients:
            Client[0].sendall(data)

    def sendAllClients(self):
        """ Sends sorted list of names & scores to all clients. """
        cursor = self.connP.execute("SELECT * from players")
        rows = cursor.fetchall()
        newlist = self.changeList(rows)
        self.sortByScore(newlist)
        print(newlist)
        data = pickle.dumps(newlist)
        for Client in self.listClients:
            Client[0].sendall("players and scores".encode('UTF-8'))
            time.sleep(0.2)
            Client[0].sendall(data)

    def changeList(self, rows):
        """ Entrance claim: Gets list of ids, names & scores.
         Exit claim: Returns a new list of names & scores. """
        newlist = []
        for i in range(len(rows)):
            newlist.append([rows[i][1], rows[i][2]])
        return newlist

    def sortByScore(self, newlist):
        """ Entrance claim: Gets list of names & scores.
        Exit claim: sorts list by score. """
        newlist.sort(key=lambda x: x[1])
        newlist.reverse()

    def closing(self, clientSocket, x):
        """ Entrance claim: Client socket, id.
         Exit claim: Delete client from self.listClients, players.db & end connection. """
        delparm = """DELETE from players where id =?"""
        for Client in self.listClients:
            if Client[0] == clientSocket:
                self.listClients.remove(Client)
        clientSocket.close()
        self.count -= 1
        self.connP.execute(delparm, (x,))

    def players_db(self):
        """ Create players table. """
        players_table = """CREATE TABLE IF NOT EXISTS players (
                                           id integer PRIMARY KEY NOT NULL,
                                           name text NOT NULL,
                                           score integer NOT NULL
                                       );"""

        cursor = self.connP.cursor()
        cursor.execute(players_table)
        self.connP.commit()

    def questionsPY_db(self):
        """ Create python questions table & Insert data into the database. """
        questionsPY_table = """CREATE TABLE IF NOT EXISTS questionsPY (
                                           id integer PRIMARY KEY NOT NULL,
                                           question text NOT NULL,
                                           answer1 text NOT NULL,
                                           answer2 text NOT NULL,
                                           answer3 text NOT NULL,
                                           answer4 text NOT NULL,
                                           rightanswer integer NOT NULL
                                       );"""

        cursor = self.connQ.cursor()
        cursor.execute(questionsPY_table)

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(1, 'What is the output of the following code?\nstr = "pynative"\n
                    print (str[1:3])', 'py', 'yn', 'pyn', 'yna', 2) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(2, 'What is the output of the following code?\nfor i in range(10, 15, 1):"
                     \n\tprint( i, end=", ")', '10, 11, 12, 13, 14,', '10, 11, 12, 13, 14, 15,',
                     '10, 11, 12, 13, 14', '10, 11, 12, 13, 14, 15', 1) ''')
        """
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(3, 'What is the output of the following code?\nvar= "James Bond"\n
                    print(var[2::-1])', 'Jam','dno', 'maJ', 'dnoB semaJ', 3) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(4, 'How do you insert comments in Python code?', '# This is a comment',
                    '// This is a comment', '/* This is a comment */', '<!-- This is a comment -->', 1) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(5, 'What is the correct file extension for Python files?', 
                    '.pyt', '.pt', '.pyth', '.py', 4) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(6, 'What is the correct syntax to output the type of a variable or object?',
                    'print(typeof(x))','print(type(x))', 'print(typeOf(x))', 'answers 1 & 2 are correct', 2) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(7, 'Which of the following is incorrect file handling mode in Python?',
                    'r', 'x', 't+', 'b', 3) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(8, 'What is the output of the following code?\ndef add(a, b):\n\treturn a+5, b+5
                    \nprint(add(3, 2))', '15', '8', '(8, 7)', 'Syntax Error', 3) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(9, 'What is the output of the following code?\nx = 75
                    \ndef myFunc():\n\tprint(x+1)\nmyFunc()', '76', '1', 'None', 'Error', 4) ''')
    
        self.connQ.execute(''' INSERT OR IGNORE INTO questionsPY(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(10, 'What is the output of the following code?\na = [10, 20]
                    \nb = a\nb += [30, 40]\nprint(a)', 'Error', '[10, 20, 30, 40]', '[40, 60]', '[10, 20]', 2) ''')
        """
        self.connQ.commit()

    def questionsIS_db(self):
        """ Create Israel questions table & Insert data into the database. """
        questionsHI_table = """CREATE TABLE IF NOT EXISTS questionsIS (
                                           id integer PRIMARY KEY NOT NULL,
                                           question text NOT NULL,
                                           answer1 text NOT NULL,
                                           answer2 text NOT NULL,
                                           answer3 text NOT NULL,
                                           answer4 text NOT NULL,
                                           rightanswer integer NOT NULL
                                       );"""

        cursor = self.connQ.cursor()
        cursor.execute(questionsHI_table)

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(1, 'Which country has no border with Israel?', 'Egypt', 'Jordan', 'Lebanon',
                    'Iraq', 4) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(2, 'Which city is the "capital of the Negev?"', 'Netivot', 'Eilat',
                     'Beer Sheva', 'Dimona', 3) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(3, 'Where from most of the water of See of Galilee is cpming from?',
                    'Jordan river', 'Mediterranean sea', 'Snir river', 'the Yarkon', 1) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(4, 'Who is buried in the Negev desert?', 'Herzel',
                    'David Ben Gurion', 'Trumpeldor', 'Yitzhak Rabin', 2) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(5, 'Who wrote the song "Jerusalem of Gold"?', 
                    'Shlomo Carlbach', 'David Broza', 'Naomi Shemer', 'Benjamin Netaniyahu', 3) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(6, 'Israelis have won the most Olympic medals in which sport?',
                    'Sailing','Kayaking', 'Wind Surfing', 'Judo', 4) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(7, 'Who was the first Israeli to win a Nobel Prize?',
                    'Dan Schechtman', 'Shai Agnon', 'Yitzhak Rabin and Shimon Peres', 'Michael Loyt', 2) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4, 
                    rightanswer) VALUES(8, 'Who is on the 50 shekels bill?', 'Haim Nachman Bialik',
                     'Haim Weizmann', 'Shaul Tchernichovsky', 'David Ben Gurion', 3) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(9, 'Which colony was named "Mother of the Colonies"?', 'Petah Tikva',
                     'Rishon Lezion', 'Ashdod', 'Nehalal', 1) ''')

        self.connQ.execute(''' INSERT OR IGNORE INTO questionsIS(id, question, answer1, answer2, answer3, answer4,
                    rightanswer) VALUES(10, 'Who was the first president of Israel?', 'David Ben Gurion',
                     'Haim Waizmann', 'Herzel', 'Azar Waizman', 2) ''')

        self.connQ.commit()


def main():
    s = Server('0.0.0.0', 4000)
    s.start()
    sys.exit()


if __name__ == '__main__':
    main()
