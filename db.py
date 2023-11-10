import sqlite3
import datetime
import pytz

current_time = datetime.datetime.now()

timezone = pytz.timezone('Europe/Moscow')

localized_time = timezone.localize(current_time)

class BotDB:
    def __init__(self, db_file):
        """Инициализация соединения с БД"""
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()


    def user_exists(self, user_id):
        """Проверка на существование юзера в БД"""

        result = self.cursor.execute('SELECT `UserID` FROM `Users` WHERE `UserID` = ?', (user_id,))
        return bool(len(result.fetchall()))

    def get_user_id(self, user_id):
        """Получаем id юзера в базе по его user_id в телеграмме"""

        result = self.cursor.execute('SELECT `UserID` FROM `Users` WHERE `UserID` = ?', (user_id,))
        return result.fetchone()[0]

    def add_user(self, user_id, user_name):
        """Добавление юзера в БД"""

        self.cursor.execute('INSERT INTO `Users` (`UserID`, `UserName`, `RegDate`) VALUES (?,?,?)',
                            (user_id, user_name, localized_time))
        return self.conn.commit()

    def add_note(self, user_id, type, amount, cat_id):
        """Создание запись о расходе/доходе"""

        self.cursor.execute('INSERT INTO `Transaction` (`UserID`, `Type`, `Amount`, `Date`,`CategoryID`) '
                            'VALUES (?,?,?,?,?)', (user_id, type, amount, localized_time, cat_id))
        return self.conn.commit()

    def get_statistic(self, user_id, within='all'):
        """Получение истории о доходах/расходах"""

        if within == 'day':
            result = self.cursor.execute('SELECT * FROM `Transaction` WHERE `UserID` = ? AND `Date` '
                                         'BETWEEN datetime("now", "start of day") AND datetime("now", "localtime") '
                                         'ORDER BY `Date`', (self.get_user_id(user_id),))
        elif within == 'week':
            result = self.cursor.execute('SELECT * FROM `Transaction` WHERE `UserID` = ? AND `Date` '
                                         'BETWEEN datetime("now", "-6 days") AND datetime("now", "localtime") '
                                         'ORDER BY `Date`', (self.get_user_id(user_id),))
        elif within == 'month':
            result = self.cursor.execute('SELECT * FROM `Transaction` WHERE `UserID` = ? AND `Date` '
                                         'BETWEEN datetime("now", "start of month") AND datetime("now", "localtime") '
                                         'ORDER BY `Date`', (self.get_user_id(user_id),))
        elif within == 'for all time':
            result = self.cursor.execute('SELECT * FROM `Transaction` WHERE `UserID` = ? '
                                         'ORDER BY `Date`', (self.get_user_id(user_id),))
        return result.fetchall()

    def get_categories_flow (self):
        """Получение списка всех категорий расходов"""
        result = self.cursor.execute('SELECT * FROM `CategoriesFlow`')
        return result.fetchall()

    def get_name_categories_flow(self, id_cat):
        """Получение названия категории расходов"""
        result = self.cursor.execute('SELECT `Name` FROM `CategoriesFlow` WHERE `CategoryID` = ? ', (id_cat,))
        return result.fetchall()

    def get_category_id(self, name_cat):
        """Получение id категории по имени"""
        result = self.cursor.execute('SELECT `CategoryID` FROM `CategoriesFlow` WHERE `Name` = ?', (name_cat,))
        return result.fetchall()

    def close(self):
        self.conn.close()
