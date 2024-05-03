import sqlite3 as sql


class DbClass:
    def __init__(self):
        self.conn = sql.connect('accounts.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                tg_id INTEGER NOT NULL,
                tw_acc TEXT,
                yt_acc TEXT
            )
        ''')

    def __enter__(self):
        return self

    def GetIdFromUsr(self, tg_id):
        self.c.execute("SELECT id FROM accounts WHERE tg_id=?", (tg_id,))
        user_id = self.c.fetchone()
        if user_id is None:
            self.c.execute("INSERT INTO accounts (tg_id) VALUES (?)", (tg_id,))
            self.conn.commit()
        self.c.execute("SELECT id FROM accounts WHERE tg_id=?", (tg_id,))
        user_id = self.c.fetchone()
        return user_id

    def GetTwAcc(self, usr_id):
        self.c.execute("SELECT tw_acc FROM accounts WHERE id=?", (usr_id,))
        user_id = self.c.fetchone()
        return user_id

    def ChangeTwAcc(self, usr_id, new_acc):
        self.c.execute('''
            UPDATE accounts
            SET tw_acc = ?
            WHERE id = ?
        ''', (new_acc, usr_id))
        self.conn.commit()

    def GetYtAcc(self, usr_id):
        self.c.execute("SELECT yt_acc FROM accounts WHERE id=?", (usr_id,))
        user_id = self.c.fetchone()
        return user_id

    def ChangeYtAcc(self, usr_id, new_acc):
        self.c.execute('''
            UPDATE accounts
            SET yt_acc = ?
            WHERE id = ?
        ''', (new_acc, usr_id))
        self.conn.commit()

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
