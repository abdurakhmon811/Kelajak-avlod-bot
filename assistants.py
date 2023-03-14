from MySQLdb.connections import Connection


class Storekeeper:
    """
    A class for generating, manipulating and retrieving data from a MySQL database.
    """

    def __init__(self, db_connection: Connection) -> None:
        """Initialize the database connection."""

        self.db = db_connection
        self.cursor = self.db.cursor()


    def table_exists(self, table_name: str) -> bool:
        """
        Checks if the given table exists in the database.
        """

        self.cursor.execute("""SHOW TABLES LIKE '%s'""" % table_name)
        if self.cursor.fetchone():
            return True
        else:
            return False


    def user_exists(self, table_name: str, pk) -> bool:
        """
        Checks if a user with the given primary key exists.
        """

        self.cursor.execute("""SELECT chat_id FROM %(table_name)s WHERE chat_id = '%(pk)s'""" % 
                            {'table_name': table_name, 'pk': pk})
        if self.cursor.fetchone():
            return True
        else:
            return False
