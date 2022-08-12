import psycopg2


def req_conditions(name="", family_name="", email=""):
    """ Вспомогательная функция """
    condition = ""
    if name != "":
        condition = " name = '" + name + "'"
    if family_name != "":
        if condition != "":
            condition += " AND"
        condition += " family_name = '" + family_name + "'"
    if email != "":
        if condition != "":
            condition += " AND"
        condition += " email = '" + email + "'"
    return condition


class ClientDB:
    # def __int__(self, db_name, user, psw):
    #     self.conn = psycopg2.connect(database=db_name, user=user, password=psw)
    #     self.cur = self.conn.cursor()

    def open(self, db_name, user, psw):
        self.conn = psycopg2.connect(database=db_name, user=user, password=psw)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def create_tables(self):
        self.cur.execute("DROP TABLE IF EXISTS phone_numbers;")
        self.cur.execute("DROP TABLE IF EXISTS clients;")

        self.cur.execute("""
                            CREATE TABLE clients(
                                id SERIAL PRIMARY KEY,
                                name VARCHAR(40) NOT NULL,
                                family_name VARCHAR(40) NOT NULL,
                                email VARCHAR(60) NOT NULL
                            ); 
                        """)
        self.cur.execute("""
                            CREATE TABLE phone_numbers(
                                id SERIAL PRIMARY KEY,
                                number VARCHAR(20) NOT NULL,
                                owner INTEGER NOT NULL REFERENCES clients(id)
                            );
                        """)
        self.conn.commit()

    def get_client_data(self, client_id):
        """ Выдает (имя, фамилия, email) клиента по id """
        self.cur.execute("SELECT name, family_name, email FROM clients WHERE id = %s;", (client_id,))
        return self.cur.fetchone()

    def find_client_id(self, name="", family_name="", email="", phone=""):
        """ Выдает список id клиентов по заданным параметрам поиска """
        cond = req_conditions(name, family_name, email)
        if cond == "" and phone == "":
            self.cur.execute("SELECT id FROM clients ORDER BY id;")
        elif cond != "" and phone == "":
            self.cur.execute("SELECT id FROM clients WHERE" + cond + ";")
        elif cond == "" and phone != "":
            self.cur.execute("SELECT owner FROM phone_numbers WHERE number = %s;", (phone,))
        else:
            self.cur.execute("""
                                SELECT p.owner FROM phone_numbers p
                                JOIN clients c
                                ON p.owner = c.id
                                WHERE
                            """ + cond + " AND number = '" + phone + "';")
        ids = self.cur.fetchall()
        return [i[0] for i in ids]

    def find_client(self, name="", family_name="", email="", phone=""):
        """ Выдает список (имя, фамилия, email) клиентов по заданным параметрам поиска """
        cond = req_conditions(name, family_name, email)
        if cond == "" and phone == "":
            self.cur.execute("SELECT name, family_name, email FROM clients ORDER BY id;")
        elif cond != "" and phone == "":
            self.cur.execute("SELECT name, family_name, email FROM clients WHERE" + cond + ";")
        elif cond == "" and phone != "":
            self.cur.execute("""
                                SELECT c.name, c.family_name, c.email
                                FROM phone_numbers p
                                JOIN clients c
                                ON p.owner = c.id
                                WHERE p.number = %s;
                            """, (phone,))
        else:
            self.cur.execute("""
                                SELECT c.name, c.family_name, c.email
                                FROM phone_numbers p
                                JOIN clients c
                                ON p.owner = c.id
                                WHERE
                             """ + cond + " AND number = '" + phone + "';")
        return self.cur.fetchall()

    def add_client(self, name, family_name, email, phones):
        """ Добавление клиента в базу """
        if name == "" or family_name == "" or email == "":
            return
        self.cur.execute("""
                            INSERT INTO clients(name, family_name, email)
                            VALUES(%s,%s,%s)
                            RETURNING id;
                        """, (name, family_name, email))
        client_id = self.cur.fetchone()
        for phone in phones:
            self.cur.execute("INSERT INTO phone_numbers(number, owner) VALUES(%s,%s);", (phone, client_id))
        self.conn.commit()

    def add_phone_to_client(self, number, name="", family_name="", email=""):
        """ Добавление телефона всем клиентам с заданными параметрами """
        client_ids = self.find_client_id(name, family_name, email)
        for id in client_ids:
            self.cur.execute("INSERT INTO phone_numbers(number, owner) VALUES(%s,%s);", (number, id))
        self.conn.commit()

    def get_client_phones(self, client_id):
        """ Выдает список телефонов клиента по id """
        self.cur.execute("SELECT number FROM phone_numbers WHERE owner = %s;", (client_id,))
        phones = self.cur.fetchall()
        return [p[0] for p in phones]

    def get_clients_number(self):
        """ Выдает общее количество клиентов """
        self.cur.execute("SELECT COUNT(id) FROM clients")
        return self.cur.fetchone()[0]

    def del_client_phones(self, name="", family_name="", email=""):
        """ Удаляет все телефоны клиентам с заданными параметрами """
        if name + family_name + email == "":
            return
        client_ids = self.find_client_id(name, family_name, email)
        for id in client_ids:
            self.cur.execute("DELETE FROM phone_numbers WHERE owner = %s;", (id,))
        self.conn.commit()

    def del_phone(self, number):
        """ Удаляет заданный телефон """
        self.cur.execute("DELETE FROM phone_numbers WHERE number = %s;", (number,))
        self.conn.commit()

    def change_client_data(self, name="", family_name="", email="", new_name="", new_family="", new_email=""):
        """ Изменение данных всех клиентов с заданными параметрами """
        client_ids = self.find_client_id(name, family_name, email)
        for id in client_ids:
            if new_name != "":
                self.cur.execute("UPDATE clients SET name = %s WHERE id = %s;", (new_name, id))
            if new_family != "":
                self.cur.execute("UPDATE clients SET family_name = %s WHERE id = %s;", (new_family, id))
            if new_email != "":
                self.cur.execute("UPDATE clients SET email = %s WHERE id = %s;", (new_email, id))
        self.conn.commit()

    def del_client(self, name="", family_name="", email=""):
        """ Удаление клиентов с заданными параметрами """
        cond = req_conditions(name, family_name, email)
        if cond != "":
            self.del_client_phones(name, family_name, email)
            self.cur.execute("DELETE FROM clients WHERE" + cond + ";")
            self.conn.commit()


with open('sql.txt') as file:
    sql_user = file.readline().strip()
    sql_psw = file.readline().strip()

my_db = ClientDB()
my_db.open("clients_db", sql_user, sql_psw )
answ = input("Создать таблицы? ")
if answ == "y" or answ == "да":
    my_db.create_tables()
print()

print("Добавление клиентов")
n = f = e = "."
while n + f + e != "":
    n = input("Введите имя: ")
    f = input("Введите фамилию: ")
    e = input("Введите email: ")
    p = []
    num = "."
    while num != "":
        num = input("Введите телефон: ")
        if num != "":
            p.append(num)
    my_db.add_client(name=n, family_name=f, email=e, phones=p)
print()

print("Поиск id")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
p = input("Введите телефон: ")
print(my_db.find_client_id(name=n, family_name=f, phone=p))
print()

print("Поиск телефонов клиента")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
client_ids = my_db.find_client_id(name=n, family_name=f)
for id in client_ids:
    print(my_db.get_client_data(id), my_db.get_client_phones(id))
print()

print("Удаление одного телефона")
my_db.del_phone(input("Введите телефон: "))
print()

print("Удаление всех телефонов клиента")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
my_db.del_client_phones(name=n, family_name=f)
print()

print("Добавление телефона клиента")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
num = input("Введите телефон: ")
my_db.add_phone_to_client(number=num, name=n, family_name=f)
print()

print("Поиск данных")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
p = input("Введите телефон: ")
print(my_db.find_client(name=n, family_name=f, phone=p))
print()

print("Изменение данных")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
new_n = input("Введите новое имя: ")
new_f = input("Введите новую фамилию: ")
new_e = input("Введите новый email: ")
my_db.change_client_data(name=n, family_name=f, new_name=new_n, new_family=new_f, new_email=new_e)
print()

print("Удаление клиента")
n = input("Введите имя: ")
f = input("Введите фамилию: ")
my_db.del_client(name=n, family_name=f)
print()

print("Все клиенты:")
print(my_db.find_client())
print("Всего клиентов -", my_db.get_clients_number())

my_db.close()
