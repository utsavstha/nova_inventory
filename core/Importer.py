import csv
import mysql.connector
from datetime import datetime
import time
import OnFloorModel
import ExternalDB
import re


class Importer:
    def __init__(self, path, fromUI=False):
        self.isTest = False  # If true all entries will be inserted to a copy table
        if fromUI:
            self.path = path
        else:
            self.path = f'{path}\\system.csv'
        self.externalDB = ExternalDB.ExternalDB()

        self.mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="ncfs",
            # password="123456",

        )

        print(self.path)

        self.cursor = self.mydb.cursor()
        self.hawb = []
        self.inserted_hawb = []  # List of HAWB that have been inserted or updated to db

        # Read file
        self.readFile()
        # print(self.hawb)

        # Insert Data
        for data in self.hawb:
            self.insert_hawb(data)

        # Clear System.csv data after it has been inserted or updated to db
        # self.clearFile()

    def clearFile(self):
        with open(self.path, 'w') as f:
            f.truncate(0)
            f.write("HAWB,PieceCount,Location,\n")
            f.close()

    def readFile(self):
        with open(self.path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count > 0:
                    if len(row) <= 3:  # Checking is ManDevan exists
                        self.hawb.append(OnFloorModel.OnFloorModel(
                            row[0], row[1], row[2]))
                    else:
                        self.hawb.append(OnFloorModel.OnFloorModel(
                            row[0], row[1], row[2], row[3]))

                line_count += 1
            csv_file.close()

    def prepare_flags_string(self, duplicate, overdue, total_sum, verified_flag, released_flag, all_clear):
        '''
        Prepares a flags string by seperating parameters by a comma
        '''
        return f"{1 if duplicate else 0}, {1 if overdue else 0}, {1 if total_sum else 0}, {1 if verified_flag else 0}, {1 if released_flag else 0}, {1 if all_clear else 0}"

    # ===========FLAGS=============

    def is_overdue_flag(self, last_imported, hawb):
        '''
        Fetches a rule about time difference from variable table,
        returns True or False based on violation of the rule
        '''
        sql_query = """SELECT value FROM python_test.Variables"""
        self.cursor.execute(sql_query)
        difference = self.cursor.fetchone()[0]
        last_date = last_imported
        devan_date = self.get_devan_date_from_external(hawb)

        if devan_date == "N.A.":
            return False
        else:
            return (last_date - devan_date).days >= difference

    def is_duplicate_flag(self, hawbObj):
        for hawb in self.inserted_hawb:
            if hawb.location == hawbObj.location and hawb.hawb == hawbObj.hawb:
                return True
        return False

    def is_verified_flag(self, hawb):
        '''
        Queries NCFS.dbo.T_HBL to check if this hawb(hbl) exists
        '''
        return self.externalDB.verify_match(hawb)
    # =============================

    def get_devan_date_from_external(self, hawb):
        '''
        Uses ExternalDB class to fetch devan date from NCFS db
        '''
        return self.externalDB.get_devan_date(hawb)

    def get_devan_date(self, hawb):
        fields_query = """SELECT table_name, column_name FROM python_test.Fields
                            WHERE onFloor_column_name = %s"""
        fields_value = ("devan_date",)
        self.cursor.execute(fields_query, fields_value)
        # Assuming there is only one rule for devan_date
        fields = self.cursor.fetchone()
        table_name = str(fields[0])
        column_name = str(fields[1])
        table_with_db = f"python_test.{table_name}"
        devan_date_query = f"SELECT {column_name} FROM {table_with_db} WHERE hawb = '{hawb}'"

        self.cursor.execute(devan_date_query)
        devan_obj = self.cursor.fetchone()
        if devan_obj is None:
            return "N.A."
        else:
            return devan_obj[0]

    def get_total_piece_count(self, hawb):
        '''
        Fetches total piece count for hbl from NCFS db
        '''
        return self.externalDB.get_piece_count(hawb)

    def insert_hawb(self, hawbObj):
        '''
        Inserts HAWB into the table, if it already exists value for lastimported
        is updated
        '''
        count_number_of_hawb_query = ""
        if self.isTest:
            count_number_of_hawb_query = f"""SELECT count(hawb), first_imported,
                                            last_imported, of_piece_count, of_location FROM
                                            `python_test`.onfloor_copy WHERE
                                            hawb = '{hawbObj.hawb}' and of_location = '{hawbObj.location}';"""
        else:
            count_number_of_hawb_query = f"""SELECT count(hawb), first_imported,
                                            last_imported, of_piece_count, of_location FROM
                                            `python_test`.onfloor WHERE
                                            hawb = '{hawbObj.hawb}' and of_location = '{hawbObj.location}';"""
        # print(count_number_of_hawb_query)
        self.cursor.execute(count_number_of_hawb_query)
        hawb_obj = self.cursor.fetchone()
        hawb_count = hawb_obj[0]
        if hawb_count > 0:
            first_imported = hawb_obj[1]
            last_imported = hawb_obj[2]
            piece_count = int(hawb_obj[3])
            of_location = hawb_obj[4]
            # Check duplicate
            is_duplicate = self.is_duplicate_flag(hawbObj)
            if not is_duplicate:
                piece_count = piece_count + int(hawbObj.pieceCount)
                of_location = f"{of_location}, {hawbObj.location}"

            # Check if the overdue rule is broken
            is_overdue = self.is_overdue_flag(last_imported, hawbObj.hawb)

            # Get total piece count
            total_piece_count = int(self.get_total_piece_count(hawbObj.hawb))

            # Flag is true is total_piece_count fetched from NCFS db is not equal to scanned piece count
            total_sum_flag = True if total_piece_count != piece_count else False

            # Retrieve devan_date
            devan_date = self.get_devan_date_from_external(hawbObj.hawb)

            # Split location from external db
            fs_location = self.externalDB.get_fs_location(hawbObj.hawb)

            # Primary location from external db
            fs_primary_location = self.externalDB.get_fs_primary_location(
                hawbObj.hawb)

            # Set true if T_CRG[F_crg_lty_code] = SUB and T_HBL[F_hbl_csn_status] = RL
            released_flag = self.externalDB.is_sub(
                hawbObj.hawb) or self.externalDB.is_rl(hawbObj.hawb)

            # Get client name from T_CLIENT
            client_name = self.externalDB.get_customer_name(hawbObj.hawb)

            # Check if hawb exists in NCFS db
            verified_flag = self.is_verified_flag(hawbObj.hawb)

            # Set true if T_CRG[F_crg_lty_code] = SUB and T_HBL[F_hbl_csn_status] = RL
            released_flag = self.externalDB.is_sub(
                hawbObj.hawb) or self.externalDB.is_rl(hawbObj.hawb)

            is_clear = (not(
                is_duplicate or is_overdue or total_sum_flag or verified_flag or released_flag))

            # If the provided hawb value already exists, update last imported date
            update_last_imported_date_query = ""
            update_in_query = ""

            release_date = self.externalDB.get_release_date(hawbObj.hawb)

            consignee = self.externalDB.get_consignee(hawbObj.hawb)

            # Insert data to duplicate table
            insert_hawb_value_query = ""

            insert_hawb_value_query = """INSERT INTO python_test.onfloor_duplicates
                                            (hawb, of_location, of_devan, of_piece_count, flags, first_imported, 
                                            last_imported, fs_devan, piece_count_difference, fs_location, fs_piece_count, fs_primary_location, client_name, release_date, consignee)
                                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            hawb_items = (hawbObj.hawb, hawbObj.location, hawbObj.ofDevan, hawbObj.pieceCount,
                          self.prepare_flags_string(
                              is_duplicate, is_overdue, total_sum_flag, verified_flag, released_flag, is_clear),
                          datetime.now(), datetime.now(), devan_date, (total_piece_count - int(hawbObj.pieceCount)), fs_location, total_piece_count, fs_primary_location, client_name, release_date, consignee)
            self.cursor.execute(insert_hawb_value_query, hawb_items)
            print("Insert to duplicates")
            if self.isTest:
                update_last_imported_date_query = f"""UPDATE python_test.OnFloor_copy SET 
                                                    of_location = '{hawbObj.location}',
                                                    of_devan = '{hawbObj.ofDevan}',
                                                    fs_devan = '{devan_date}',
                                                    fs_location = '{fs_location}',
                                                    fs_piece_count = '{total_piece_count}',
                                                    fs_primary_location = '{fs_primary_location}',
                                                    last_imported = '{datetime.now()}',
                                                    of_piece_count = '{piece_count}',
                                                    piece_count_difference = '{total_piece_count - piece_count}',
                                                    release_date = '{release_date}',
                                                    consignee = '{consignee}',
                                                    flags='{self.prepare_flags_string(
                                                        is_duplicate, is_overdue, total_sum_flag, verified_flag, released_flag, is_clear
                                                    )}' WHERE hawb = '{hawbObj.hawb}'
                                                    """
            else:
                update_last_imported_date_query = f"""UPDATE python_test.OnFloor SET 
                                                    of_location = '{hawbObj.location}',
                                                    of_devan = '{hawbObj.ofDevan}',
                                                    fs_devan = '{devan_date}',
                                                    fs_location = '{fs_location}',
                                                    fs_piece_count = '{total_piece_count}',
                                                    fs_primary_location = '{fs_primary_location}',
                                                    last_imported = '{datetime.now()}',
                                                    of_piece_count = '{piece_count}',
                                                    piece_count_difference = '{total_piece_count - piece_count}',
                                                    release_date = '{release_date}',
                                                    consignee = '{consignee}',
                                                    flags='{self.prepare_flags_string(
                                                        is_duplicate, is_overdue, total_sum_flag, verified_flag, released_flag, is_clear
                                                    )}' WHERE hawb = '{hawbObj.hawb}'
                                                    """
                # update_in_query = f"""
                # UPDATE python_test.onfloor_in SET python_test.onfloor_in.onfloor_in_piece_count =
                #  python_test.onfloor_in.onfloor_in_piece_count + 1 WHERE (python_test.onfloor_in.onfloor_in_uid
                #   = (SELECT uuid FROM onfloor WHERE hawb = '{hawbObj.hawb}') AND python_test.onfloor_in.onfloor_in_id <> 0);
                # """
            # print(update_last_imported_date_query)
            self.cursor.execute(update_last_imported_date_query)
            # self.cursor.execute(update_in_query)

        else:
            # Check duplicate
            is_duplicate = self.is_duplicate_flag(hawbObj)

            # Since this is a new entry overdue is not possible
            is_overdue = False

            # Retrieve devan_date
            devan_date = self.get_devan_date_from_external(hawbObj.hawb)

            # Get total piece count
            total_piece_count = int(self.get_total_piece_count(hawbObj.hawb))

            # Flag is true is total_piece_count fetched from NCFS db is not equal to scanned piece count
            total_sum_flag = (total_piece_count - int(hawbObj.pieceCount)) != 0

            # Check if hawb exists in NCFS db
            verified_flag = self.is_verified_flag(hawbObj.hawb)

            # Split location from external db
            fs_location = self.externalDB.get_fs_location(hawbObj.hawb)

            # Primary location from external db
            fs_primary_location = self.externalDB.get_fs_primary_location(
                hawbObj.hawb)

            # Set true if T_CRG[F_crg_lty_code] = SUB and T_HBL[F_hbl_csn_status] = RL
            released_flag = self.externalDB.is_sub(
                hawbObj.hawb) or self.externalDB.is_rl(hawbObj.hawb)

            # Get client name from T_CLIENT
            client_name = self.externalDB.get_customer_name(hawbObj.hawb)

            is_clear = (not(
                is_duplicate or is_overdue or total_sum_flag or verified_flag or released_flag))

            release_date = self.externalDB.get_release_date(hawbObj.hawb)

            consignee = self.externalDB.get_consignee(hawbObj.hawb)

            # If the provided hawb value doesnt already exist, insert a new one
            insert_hawb_value_query = ""
            insert_in_hawb_value_query = ""

            if self.isTest:
                insert_hawb_value_query = """INSERT INTO python_test.OnFloor_copy
                                            (hawb, of_location, of_devan, of_piece_count, flags, first_imported, 
                                            last_imported, fs_devan, piece_count_difference, fs_location, fs_piece_count, fs_primary_location, client_name)
                                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            else:
                insert_hawb_value_query = """INSERT INTO python_test.OnFloor
                                            (hawb, of_location, of_devan, of_piece_count, flags, first_imported, 
                                            last_imported, fs_devan, piece_count_difference, fs_location, fs_piece_count, fs_primary_location, client_name, release_date, consignee)
                                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            hawb_items = (hawbObj.hawb, hawbObj.location, hawbObj.ofDevan, hawbObj.pieceCount,
                          self.prepare_flags_string(
                              is_duplicate, is_overdue, total_sum_flag, verified_flag, released_flag, is_clear),
                          datetime.now(), datetime.now(), devan_date, (total_piece_count - int(hawbObj.pieceCount)), fs_location, total_piece_count, fs_primary_location, client_name, release_date, consignee)
            self.cursor.execute(insert_hawb_value_query, hawb_items)
            # last_id = self.cursor.execute("SELECT MAX(uuid) FROM python_test.onfloor")
            # insert_in_hawb_value_query = """INSERT INTO python_test.onfloor_in (onfloor_in_uid, onfloor_in_piece_count, onfloor_in_last_scanned) values(%s, %s, %s); """
            # in_items = (last_id,hawbObj.pieceCount, datetime.now())
            # self.cursor.execute(insert_in_hawb_value_query, in_items)
        self.inserted_hawb.append(hawbObj)
        self.mydb.commit()
