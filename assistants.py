from MySQLdb.connections import Connection
from MySQLdb._exceptions import Error, OperationalError
import MySQLdb as msdb
import random as rm
import re
import time


class DB:
    """
    A class for manipulating database.
    """

    def make_connection(self) -> Connection:
        """
        Connects to the database.
        """

        try:
            db: Connection = msdb.connect(
                host='',
                database='',
                user='',
                password=''
            )
        except Error as e:
            print('An error happened while trying to connect to the database: ', e)
        else:
            print('Database connection made successfully!')
            return db

    
    def close_connection(self, connection: Connection, cursor: msdb.cursors.Cursor):
        """
        Closes the opened connection along with the cursor.
        """

        cursor.close()
        connection.close()
        print('Database connection closed successfully!')


class Channel:
    """
    A class for modeling channels.
    """

    def get_channel(self, link: str = None, latest: bool = True) -> dict:
        """
        Retrieves the data about the channel with the primary key and returns a dictionary containing the data.
        """

        db = DB()

        result = None
        if not link and latest is True:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute(
                """SELECT * FROM channels ORDER BY date_added DESC LIMIT 1"""
            )
            result = cursor.fetchone()
        elif link and latest is False:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute(
                """SELECT * FROM channels WHERE username = '%s'""" % link
            )
            result = cursor.fetchone()
        else:
            raise ValueError(
                'You cannot pass LINK and set LATEST to True simultaneously! Pass LINK or set latest to True!'
            )
        db.close_connection(connection, cursor)
        if result:
            resulting_dict = {
                'username': result[0],
                'date_added': result[1],
            }
            return resulting_dict
        return None


    def get_channel_usernames(self) -> tuple:
        """
        Retrieves all channel usernames that exist in the database.
        """

        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute("""SELECT username FROM channels""")
        results = cursor.fetchall()
        db.close_connection(connection, cursor)
        return [each[0] for each in results] if results else None


class DBFactory:
    """
    A class for creating tables and modifying them.
    """

    def charfield(self, field_name: str, max_length: int, long_text: bool = False, default: str = None) -> str:
        """
        Creates a character field, which is ideally for short text.

        :param: field_name: Accepts a string type of the name for the column.
        :param: max_length: Accepts an integer for defining the maximum length of text value.
        :param: long_text: If true VARCHAR type is created else CHAR.
        :param: default: Defaults to None, accepts a default value for the field.
        :returns: A string containing an SQL statement to create a field in the database.
        """

        if not long_text:
            without_default = (field_name, max_length)
            with_default = (field_name, max_length, default)
            return "%s CHAR(%d)" % without_default if not default else "%s CHAR(%d) DEFAULT '%s'" % with_default
        else:
            without_default = (field_name, max_length)
            with_default = (field_name, max_length, default)
            return "%s VARCHAR(%d)" % without_default if not default else "%s VARCHAR(%d) DEFAULT '%s'" % with_default
    

    def create_table(self, table_name, *args):
        """
        Creates a table with the specified name.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        table_definition = {
            'table_name': table_name,
            'columns': ', '.join([arg for arg in args])
        }
        cursor.execute("""CREATE TABLE %(table_name)s (%(columns)s)""" % table_definition)
        connection.commit()
        db.close_connection(connection, cursor)
    

    def set_constraint(self, constraint_name: str, for_column: str, constraint_type: str = 'PRIMARY KEY'):
        """
        Sets a constraint for the given column.

        Available constraint types:
            1. PRIMARY KEY - which is the default here.
            2. FOREIGN KEY.
            3. UNIQUE.
            4. CHECK.
        NOTE: The constraint type string should be all in upper case.
        """

        return "CONSTRAINT %s %s (%s)" % (constraint_name, constraint_type, for_column)
    

    def datetimefield(self, field_name: str, date_only: bool = False):
        """
        Creates a date or datetime field.

        :param: field_name: Accepts a string type of the name for the column.
        :param: date_only: Set this parameter to True if you want to datefield rather than datetime field.
        :returns: A string containing an SQL statement to create a field in the database.
        """

        return "%s DATETIME" % field_name if not date_only else "%s DATE" % field_name


    def integerfield(self, 
                     field_name: str, 
                     int_type: str = 'integer',
                     default: int = 0) -> str:
        """
        Creates an integer field.

        Specify the type of the field setting int_type parameter - which defaults to INTEGER - to the following values:
            1. tinyint
            2. smallint
            3. mediumint
            4. integer
            5. bigint

        :param: field_name: Accepts a string type of the name for the column.
        :param: default: Defaults to 0, accepts a default value for the field.
        :returns: A string containing an SQL statement to create a field in the database.
        """

        if int_type.lower() == 'tinyint':
            return "%s TINYINT DEFAULT %d" % (field_name, default)
        elif int_type.lower() == 'smallint':
            return "%s SMALLINT DEFAULT %d" % (field_name, default)
        elif int_type.lower() == 'mediumint':
            return "%s MEDIUMINT DEFAULT %d" % (field_name, default)
        elif int_type.lower() == 'integer':
            return "%s INT DEFAULT %d" % (field_name, default)
        elif int_type.lower() == 'bigint':
            return "%s BIGINT DEFAULT %d" % (field_name, default)
        else:
            raise TypeError("Invalid integer type! Please check out the description of the integerfield method.")


class Storekeeper:
    """
    A class for generating, manipulating and retrieving data from a MySQL database.
    """

    def drop_table(self, table_name: str):
        """
        Drops/Removes the given table from the database.
        """
        
        db = DB()
        
        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        try:
            cursor.execute("""DROP TABLE %s""" % table_name)
        except OperationalError:
            raise ValueError("Invalid table name!")
        finally:
            db.close_connection(connection, cursor)
    

    def get_supplies(self, table_name: str, columns: list | tuple, values: list | tuple):
        """
        Inserts the given values into the given columns of the given table.

        NOTE: the length of columns and values should correspond to each other, otherwise ValueError is raised.
        """

        db = DB()
        
        if len(columns) == len(values):
            columns = ["{}".format(column) for column in columns]
            values = ["'{}'".format(value) for value in values]
            columns = ', '.join(columns)
            values = ', '.join(values)
            entries = {
                'table_name': table_name,
                'columns': columns,
                'values': values,
            }
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute("""INSERT INTO %(table_name)s (%(columns)s) VALUES (%(values)s)""" % entries)
            connection.commit()
            db.close_connection(connection, cursor)
        else:
            raise ValueError('Invalid number of columns and values! The length of the two does not correspond.')
    

    def table_exists(self, table_name: str) -> bool:
        """
        Checks if the given table exists in the database.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute("""SHOW TABLES LIKE '%s'""" % table_name)
        result = cursor.fetchone()
        db.close_connection(connection, cursor)
        return True if result else False
    

    def throw_item_away(self, table_name: str, pk_name: str, pk_value: str | int):
        """
        Deletes an item corresponding to the given primary key from a row in the given table.
        """
        
        db = DB()
        
        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute("""DELETE FROM {} WHERE {} = '{}';""".format(table_name, pk_name, pk_value))
        connection.commit()
        db.close_connection(connection, cursor)


class Test:
    """
    A class for modeling tests.
    """

    def deactivate(self, test_id: str):
        """
        Sets the is_active attribute of a test to 0(False).
        """

        db = DB()

        test = self.get_test(test_id)
        if test is not None:
            if int(test['is_active']) == True:
                connection = db.make_connection()
                cursor: msdb.cursors.Cursor = connection.cursor()
                now = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
                cursor.execute(
                    """UPDATE tests SET is_active = 0, date_deactivated = '%s' WHERE test_id = '%s'""" % \
                    (now, test_id)
                )
                connection.commit()
                db.close_connection(connection, cursor)
            else:
                raise AttributeError('The test is already deactivated!')
        else:
            raise ValueError('Test with the given id does not exist!')
    

    def get_all_test_ids(self) -> list:
        """
        Retrieves all the ids related to test from the the database.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute("""SELECT test_id FROM tests""")
        results = cursor.fetchall()
        db.close_connection(connection, cursor)
        return list(results) if results else None
    

    def get_test(self, test_id: str) -> dict:
        """
        Retrieves the data about the test with the primary key and returns a dictionary containing the data.
        """

        db = DB()

        if test_id:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute("""SELECT * FROM tests WHERE test_id = '%s'""" % test_id)
            result = cursor.fetchone()
            db.close_connection(connection, cursor)
            if result:
                resulting_dict = {
                    'test_id': result[0],
                    'test_subject': result[1],
                    'creator': result[2],
                    'answers': result[3],
                    'start_date': result[4],
                    'end_date': result[5],
                    'is_active': True if int(result[6]) == 1 else False,
                }
                return resulting_dict
        return None
    

    def get_tests(self) -> list:
        """
        Retrieves all the tests from the database.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute("""SELECT * FROM tests""")
        results = cursor.fetchall()
        db.close_connection(connection, cursor)
        output = []
        if results:
            for result in results:
                out_dict = {
                    'test_id': result[0],
                    'test_subject': result[1],
                    'creator': result[2],
                    'answers': result[3],
                    'date_created': result[4],
                    'date_deactivated': result[5],
                    'is_active': True if int(result[6]) == 1 else False,
                }
                output.append(out_dict)
            return output
        return None 


class TestResult:
    """
    A class for modeling test results.
    """

    def get_results(self, test_id: str) -> list:
        """
        Retrieves the test results with corresponding test id or creator, or gets all in the database.
        """

        db = DB()

        if test_id:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute(
                """SELECT test_taker, correct_answers, user_answers  FROM test_results WHERE test_id = '%s' """ \
                "ORDER BY correct_answers DESC" % test_id
            )
            results = cursor.fetchall()
            db.close_connection(connection, cursor)
            if results:
                resulting = []
                for result in results:
                    out_dict = {
                        'test_taker': result[0],
                        'correct_answers': result[1],
                        'user_answers': result[2],
                    }
                    resulting.append(out_dict)
                return resulting
            return None


class User:
    """
    A class for modeling bot users.
    """

    def change_name(self, user_id: str, name: str):
        """
        Changes the user's name.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute(
            """UPDATE users SET name = '%s' WHERE chat_id = '%s'""" % \
            (name, user_id)
        )
        connection.commit()
        db.close_connection(connection, cursor)


    def change_phone_number(self, user_id: str, phone_number: str):
        """
        Changes the user's phone number.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute(
            """UPDATE users SET phone_number = '%s' WHERE chat_id = '%s'""" % \
            (phone_number, user_id)
        )
        connection.commit()
        db.close_connection(connection, cursor)


    def change_school(self, user_id: str, school: str):
        """
        Changes the user's school.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute(
            """UPDATE users SET school = '%s' WHERE chat_id = '%s'""" % \
            (school, user_id)
        )
        connection.commit()
        db.close_connection(connection, cursor)

    
    def delete_user(self, user_id: str):
        """
        Deletes the specified user from the database.
        """
        
        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute(
            """DELETE FROM users WHERE chat_id = '%s'""" % user_id
        )
        connection.commit()
        db.close_connection(connection, cursor)
    

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieves the user with the corresponding name.
        """

        db = DB()

        if name:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute("""SELECT * FROM users WHERE name = '%s'""" % name)
            result = cursor.fetchone()
            db.close_connection(connection, cursor)
            if result:
                out_dict = {
                    'chat_id': result[0],
                    'name': result[1],
                    'phone_number': result[2],
                    'school': result[3],
                    'username': "Mavjud emas" if result[4] == 'None' else result[4],
                    'is_superuser': True if int(result[5]) == 1 else False,
                    'is_admin': True if int(result[6]) == 1 else False,
                }
                return out_dict
            return None
    

    def get_user_or_users(
            self, 
            pk_name: str = None, 
            pk_value: str = None, 
            all: bool = False, 
            many: bool = False
    ) -> (dict | list):
        """
        Retrieves the data about the user or users with the given primary key and 
        returns a dictionary containing the data.

        Set many to True if you want to get a number of users with the same primary key.
        """

        db = DB()

        if pk_name and pk_value and all is False and many is False:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute("""SELECT * FROM users WHERE {} = '{}'""".format(pk_name, pk_value))
            result = cursor.fetchone()
            db.close_connection(connection, cursor)
            if result:
                resulting_dict = {
                    'chat_id': result[0],
                    'name': result[1],
                    'phone_number': result[2],
                    'school': result[3],
                    'username': "Mavjud emas" if result[4] == 'None' else result[4],
                    'is_superuser': True if int(result[5]) == 1 else False,
                    'is_admin': True if int(result[6]) == 1 else False,
                }
                return resulting_dict
        elif not pk_name and not pk_value and all is True and many is False:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute("""SELECT * FROM users""")
            results = cursor.fetchall()
            db.close_connection(connection, cursor)
            output = []
            if results:
                for result in results:
                    resulting_dict = {
                        'chat_id': result[0],
                        'name': result[1],
                        'phone_number': result[2],
                        'school': result[3],
                        'username': "Mavjud emas" if result[4] == 'None' else result[4],
                        'is_superuser': True if int(result[5]) == 1 else False,
                        'is_admin': True if int(result[6]) == 1 else False,
                    }
                    output.append(resulting_dict)
                return output
        elif pk_name and pk_value and all is False and many is True:
            connection = db.make_connection()
            cursor: msdb.cursors.Cursor = connection.cursor()
            cursor.execute("""SELECT * FROM users WHERE {} = '{}'""".format(pk_name, pk_value))
            results = cursor.fetchall()
            db.close_connection(connection, cursor)
            output = []
            if results:
                for result in results:
                    resulting_dict = {
                        'chat_id': result[0],
                        'name': result[1],
                        'phone_number': result[2],
                        'school': result[3],
                        'username': "Mavjud emas" if result[4] == 'None' else result[4],
                        'is_superuser': True if int(result[5]) == 1 else False,
                        'is_admin': True if int(result[6]) == 1 else False,
                    }
                    output.append(resulting_dict)
                return output
        return None
    

    def get_users_count(self) -> int:
        """
        Returns the number of all available users.
        """

        db = DB()

        connection = db.make_connection()
        cursor: msdb.cursors.Cursor = connection.cursor()
        cursor.execute("""SELECT chat_id FROM users""")
        results = cursor.fetchall()
        db.close_connection(connection, cursor)
        return len(results)


    def promote_to_admin(self, chat_id: str):
        """
        Sets the is_admin attribute of a user to 1(True).
        """

        db = DB()

        user = self.get_user_or_users('chat_id', chat_id)
        if user is not None:
            if int(user['is_admin']) == False:
                connection = db.make_connection()
                cursor: msdb.cursors.Cursor = connection.cursor()
                cursor.execute("""UPDATE users SET is_admin = 1 WHERE chat_id = '%s'""" % chat_id)
                connection.commit()
                db.close_connection(connection, cursor)
            else:
                raise AttributeError('The user is already an admin!')
        else:
            raise ValueError('User with the given id does not exist!')
    

    def promote_to_superuser(self, chat_id):
        """
        Sets the is_superuser attribute of a user to 1(True).
        """

        db = DB()

        user = self.get_user_or_users('chat_id', chat_id)
        if user is not None:
            if int(user['is_superuser']) == False:
                connection = db.make_connection()
                cursor: msdb.cursors.Cursor = connection.cursor()
                cursor.execute("""UPDATE users SET is_superuser = 1, is_admin = 1 WHERE chat_id = '%d'""" % chat_id)
                connection.commit()
                db.close_connection(connection, cursor)
            else:
                raise AttributeError('The user is already a superuser!')
        else:
            raise ValueError('User with the given id does not exist!')


def get_items_in_dict(items: list | tuple) -> dict:
    """
    Places every item in a list to a dict as {index: value} key-value pairs.
    """

    output = {}
    for index, value in enumerate(items):
        output[index + 1] = value
    
    return output


def get_percent(x: int, y: int) -> int | float:
    """
    Returns the percentage of x relative to y.
    """

    return (x / y) * 100


def get_test_code(code_length: int, present_codes: list | tuple):
    """
    Generates a new code that does not exist in the database.
    """

    while True:
        code = random_word(code_length, digits_only=True)
        if present_codes and code in present_codes:
            continue
        else:
            return code


def item_has_space(array: list) -> bool:
    """
    Returns a boolean value based on the result if any item in a list contains space or not.
    """

    space = re.compile(r'\s')
    for item in array:
        if space.search(item):
            return True
    
    return False


def name_valid(items: list | tuple) -> bool:
    """
    Validates name.
    """

    result = None
    for item in items:
        if not re.findall(r"[^a-zA-Z\\s:'’`-]", item):
            result = True
        else:
            result = False
            break
    
    return result


def random_word(
        length: int, 
        digits_only: bool = False, 
        letters_only: bool = False,
        lower_letters_only: bool = False,
        upper_letters_only: bool = False
    ) -> str:
    """
    Creates a random password.
    """

    lower_letters = 'abcdefghijklmnopqrstuvwxyz'
    upper_letters = lower_letters.upper()
    digits = '0123456789'
    characters = digits + lower_letters + upper_letters

    result = ''
    while len(result) < length:
        if digits_only is False and letters_only is False and lower_letters_only is False and upper_letters_only is False:
            chosen = rm.choice(characters)
        elif digits_only is True and letters_only is False and lower_letters_only is False and upper_letters_only is False:
            chosen = rm.choice(digits)
        elif digits_only is False and letters_only is True and lower_letters_only is False and upper_letters_only is False:
            chosen = rm.choice(lower_letters + upper_letters)
        elif digits_only is False and letters_only is False and lower_letters_only is True and upper_letters_only is False:
            chosen = rm.choice(lower_letters)
        elif digits_only is False and letters_only is False and lower_letters_only is False and upper_letters_only is True:
            chosen = rm.choice(upper_letters)
        else:
            raise ValueError("You cannot set more than one password modes to True!")
        result += chosen
    
    return result


def separate_by(string: str, separator: str) -> str:
    """
    Returns a string the characters of which is separated by comma.
    """

    output = ''
    for each in string:
        each += separator
        output += each
    resulting = output.rstrip(',')

    return resulting


def space_exists(string: str) -> bool:
    """
    Returns a boolean value based on the result if the given string contains space or not.
    """

    space = re.compile(r'\s')
    return True if space.search(string) else False
