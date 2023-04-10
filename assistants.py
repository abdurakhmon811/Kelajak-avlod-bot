from MySQLdb.connections import Connection
from MySQLdb._exceptions import OperationalError
import random as rm
import re
import time


class Channel:
    """
    A class for modeling channels.
    """

    def __init__(self, db_connection: Connection):
        """Initialize the database connection."""

        self.db = db_connection
    

    def get_channel(self, link: str = None, latest: bool = True) -> dict:
        """
        Retrieves the data about the channel with the primary key and returns a dictionary containing the data.
        """

        if not link and latest is True:
            cursor = self.db.cursor()
            cursor.execute(
                """SELECT * FROM channels ORDER BY date_added DESC LIMIT 1"""
            )
        elif link and latest is False:
            cursor = self.db.cursor()
            cursor.execute(
                """SELECT * FROM channels WHERE username = '%s'""" % link
            )
        else:
            raise ValueError(
                'You cannot pass LINK and set LATEST to True simultaneously! Pass LINK or set latest to True!'
            )
        result = cursor.fetchone()
        cursor.close()
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

        cursor = self.db.cursor()

        cursor.execute("""SELECT username FROM channels""")
        results = cursor.fetchall()
        cursor.close()
        return [each[0] for each in results] if results else None


class DBFactory:
    """
    A class for creating tables and modifying them.
    """

    def __init__(self, db_connection: Connection) -> None:
        """Initialize the connection"""

        self.db = db_connection
    

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
        
        cursor = self.db.cursor()

        table_definition = {
            'table_name': table_name,
            'columns': ', '.join([arg for arg in args])
        }
        cursor.execute("""CREATE TABLE %(table_name)s (%(columns)s)""" % table_definition)
        self.db.commit()
        cursor.close()
    

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

    def __init__(self, db_connection: Connection):
        """Initialize the database connection."""

        self.db = db_connection


    def drop_table(self, table_name: str):
        """
        Drops/Removes the given table from the database.
        """
        
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""DROP TABLE %s""" % table_name)
        except OperationalError:
            raise ValueError("Invalid table name!")
        finally:
            cursor.close()
    

    def get_supplies(self, table_name: str, columns: list | tuple, values: list | tuple):
        """
        Inserts the given values into the given columns of the given table.

        NOTE: the length of columns and values should correspond to each other, otherwise ValueError is raised.
        """
        
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
            cursor = self.db.cursor()
            cursor.execute("""INSERT INTO %(table_name)s (%(columns)s) VALUES (%(values)s)""" % entries)
            self.db.commit()
            cursor.close()
        else:
            raise ValueError('Invalid number of columns and values! The length of the two does not correspond.')
    

    def table_exists(self, table_name: str) -> bool:
        """
        Checks if the given table exists in the database.
        """
        
        cursor = self.db.cursor()

        cursor.execute("""SHOW TABLES LIKE '%s'""" % table_name)
        result = cursor.fetchone()
        cursor.close()
        return True if result else False
    

    def throw_item_away(self, table_name: str, pk_name: str, pk_value: str | int):
        """
        Deletes an item corresponding to the given primary key from a row in the given table.
        """
        
        cursor = self.db.cursor()
        
        cursor.execute("""DELETE FROM {} WHERE {} = '{}';""".format(table_name, pk_name, pk_value))
        self.db.commit()
        cursor.close()


class Test:
    """
    A class for modeling tests.
    """

    def __init__(self, db_connection: Connection):
        """Initialize the database connection."""

        self.db = db_connection
    

    def deactivate(self, test_id: str):
        """
        Sets the is_active attribute of a test to 0(False).
        """

        test = self.get_test(test_id)
        if test is not None:
            if int(test['is_active']) == True:
                cursor = self.db.cursor()
                now = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
                cursor.execute(
                    """UPDATE tests SET is_active = 0, date_deactivated = '%s' WHERE test_id = '%s'""" % \
                    (now, test_id)
                )
                self.db.commit()
                cursor.close()
            else:
                raise AttributeError('The test is already deactivated!')
        else:
            raise ValueError('Test with the given id does not exist!')
    

    def get_all_test_ids(self) -> list:
        """
        Retrieves all the ids related to test from the the database.
        """
        
        cursor = self.db.cursor()

        cursor.execute("""SELECT test_id FROM tests""")
        results = cursor.fetchall()
        cursor.close()
        return list(results) if results else None
    

    def get_test(self, test_id: str) -> dict:
        """
        Retrieves the data about the test with the primary key and returns a dictionary containing the data.
        """

        if test_id:
            cursor = self.db.cursor()
            cursor.execute("""SELECT * FROM tests WHERE test_id = '%s'""" % test_id)
            result = cursor.fetchone()
            cursor.close()
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
    

    def get_tests(self, is_active: bool = True) -> list:
        """
        Retrieves all the tests(either the active ones or not active ones) from the database.
        """
        
        cursor = self.db.cursor()

        output = []
        cursor.execute("""SELECT * FROM tests""")
        results = cursor.fetchall()
        cursor.close()
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

    def __init__(self, db_connection: Connection):
        """Initialize the database connection"""

        self.db = db_connection
    

    def get_results(self, test_id: str) -> list:
        """
        Retrieves the test results with corresponding test id or creator, or gets all in the database.
        """

        if test_id:
            cursor = self.db.cursor()
            cursor.execute(
                """SELECT test_taker, correct_answers, user_answers  FROM test_results WHERE test_id = '%s' """ \
                "ORDER BY correct_answers DESC" % test_id
            )
            results = cursor.fetchall()
            cursor.close()
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

    def __init__(self, db_connection: Connection):
        """Initialize the database connection."""
    
        self.db = db_connection
    

    def change_name(self, user_id: str, first_name: str, last_name: str):
        """
        Changes the user's names.
        """
        
        cursor = self.db.cursor()

        cursor.execute(
            """UPDATE users SET fname = '%s', lname = '%s' WHERE chat_id = '%s'""" % \
            (first_name, last_name, user_id)
        )
        self.db.commit()
        cursor.close()


    def change_phone_number(self, user_id: str, phone_number: str):
        """
        Changes the user's phone number.
        """
        
        cursor = self.db.cursor()

        cursor.execute(
            """UPDATE users SET phone_number = '%s' WHERE chat_id = '%s'""" % \
            (phone_number, user_id)
        )
        self.db.commit()
        cursor.close()
    
    
    def change_address(self, user_id: str, address: str):
        """
        Changes the user's address.
        """
        
        cursor = self.db.cursor()

        cursor.execute(
            """UPDATE users SET address = '%s' WHERE chat_id = '%s'""" % \
            (address, user_id)
        )
        self.db.commit()
        cursor.close()


    def change_school(self, user_id: str, school: str):
        """
        Changes the user's school.
        """
        
        cursor = self.db.cursor()

        cursor.execute(
            """UPDATE users SET school = '%s' WHERE chat_id = '%s'""" % \
            (school, user_id)
        )
        self.db.commit()
        cursor.close()
    

    def change_class(self, user_id: str, class_: str):
        """
        Changes the user's class.
        """
        
        cursor = self.db.cursor()

        cursor.execute(
            """UPDATE users SET class = '%s' WHERE chat_id = '%s'""" % \
            (class_, user_id)
        )
        self.db.commit()
        cursor.close()

    
    def delete_user(self, user_id: str):
        """
        Deletes the specified user from the database.
        """
        
        cursor = self.db.cursor()

        cursor.execute(
            """DELETE FROM users WHERE chat_id = '%s'""" % user_id
        )
        self.db.commit()
        cursor.close()
    

    def get_user_by_name(self, first_name: str, last_name: str) -> dict:
        """
        Retrieves the user with the corresponding given names.
        """

        if first_name and last_name:
            cursor = self.db.cursor()
            cursor.execute("""SELECT * FROM users WHERE fname = '%s' AND lname = '%s'""" % (first_name, last_name))
            result = cursor.fetchone()
            cursor.close()
            if result:
                out_dict = {
                    'chat_id': result[0],
                    'first_name': result[1],
                    'last_name': result[2],
                    'phone_number': result[3],
                    'address': result[4],
                    'school': result[5],
                    'class': result[6],
                    'username': "Mavjud emas" if result[7] == 'None' else result[7],
                    'is_superuser': True if int(result[8]) == 1 else False,
                    'is_admin': True if int(result[9]) == 1 else False,
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

        

        if pk_name and pk_value and all is False and many is False:
            cursor = self.db.cursor()
            cursor.execute("""SELECT * FROM users WHERE {} = '{}'""".format(pk_name, pk_value))
            result = cursor.fetchone()
            cursor.close()
            if result:
                resulting_dict = {
                    'chat_id': result[0],
                    'first_name': result[1],
                    'last_name': result[2],
                    'phone_number': result[3],
                    'address': result[4],
                    'school': result[5],
                    'class': result[6],
                    'username': "Mavjud emas" if result[7] == 'None' else result[7],
                    'is_superuser': True if int(result[8]) == 1 else False,
                    'is_admin': True if int(result[9]) == 1 else False,
                }
                return resulting_dict
        elif not pk_name and not pk_value and all is True and many is False:
            cursor = self.db.cursor()
            cursor.execute("""SELECT * FROM users""")
            results = cursor.fetchall()
            cursor.close()
            output = []
            if results:
                for result in results:
                    resulting_dict = {
                        'chat_id': result[0],
                        'first_name': result[1],
                        'last_name': result[2],
                        'phone_number': result[3],
                        'address': result[4],
                        'school': result[5],
                        'class': result[6],
                        'username': "Mavjud emas" if result[7] == 'None' else result[7],
                        'is_superuser': True if int(result[8]) == 1 else False,
                        'is_admin': True if int(result[9]) == 1 else False,
                    }
                    output.append(resulting_dict)
                return output
        elif pk_name and pk_value and all is False and many is True:
            cursor = self.db.cursor()
            cursor.execute("""SELECT * FROM users WHERE {} = '{}'""".format(pk_name, pk_value))
            results = cursor.fetchall()
            cursor.close()
            out = []
            if results:
                for result in results:
                    resulting_dict = {
                        'chat_id': result[0],
                        'first_name': result[1],
                        'last_name': result[2],
                        'phone_number': result[3],
                        'address': result[4],
                        'school': result[5],
                        'class': result[6],
                        'username': "Mavjud emas" if result[7] == 'None' else result[7],
                        'is_superuser': True if int(result[8]) == 1 else False,
                        'is_admin': True if int(result[9]) == 1 else False,
                    }
                    out.append(resulting_dict)
                return out
        return None
    

    def get_users_count(self) -> int:
        """
        Returns the number of all available users.
        """

        cursor = self.db.cursor()

        cursor.execute("""SELECT chat_id FROM users""")
        results = cursor.fetchall()
        cursor.close()
        return len(results)


    def promote_to_admin(self, chat_id: str):
        """
        Sets the is_admin attribute of a user to 1(True).
        """

        user = self.get_user_or_users('chat_id', chat_id)
        if user is not None:
            if int(user['is_admin']) == False:
                cursor = self.db.cursor()
                cursor.execute("""UPDATE users SET is_admin = 1 WHERE chat_id = '%s'""" % chat_id)
                self.db.commit()
                cursor.close()
            else:
                raise AttributeError('The user is already an admin!')
        else:
            raise ValueError('User with the given id does not exist!')
    

    def promote_to_superuser(self, chat_id):
        """
        Sets the is_superuser attribute of a user to 1(True).
        """

        user = self.get_user_or_users('chat_id', chat_id)
        if user is not None:
            if int(user['is_superuser']) == False:
                cursor = self.db.cursor()
                cursor.execute("""UPDATE users SET is_superuser = 1, is_admin = 1 WHERE chat_id = '%d'""" % chat_id)
                self.db.commit()
                cursor.close()
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


def names_valid(items: list | tuple) -> bool:
    """
    Validates names.
    """

    result = None
    for item in items:
        if (
            not re.findall(r'[^a-zA-Z:]', item) and 
            (str(item).lower().startswith('f:') or str(item).lower().startswith('i:'))
        ):
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
