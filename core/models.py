from django.db import models
from django.db import connection
from core.Record import Record


class AuditRecords(models.Model):
    def getFlags(self, flagString):
        return flagString.split(",")

    def search(self, keyword):
        with connection.cursor() as cursor:
            try:
                cursor.execute(f"SELECT * FROM onfloor WHERE hawb LIKE '%{keyword}%'")
                results = cursor.fetchall()
                records = []
                for result in results:
                    records.append(Record(
                        result[0],
                        result[1],
                        self.getFlags(result[2]),
                        result[3],
                        result[4],
                        result[5],
                        result[6],
                        result[7],
                        result[8],
                        result[9],
                        result[10],
                        result[11],
                        result[12],
                        result[13],
                        result[14],
                        result[15])
                    )
                return records
            except err:
                print(err)

    def all(self, keyword="", page=-1, limit=-1, last_imported_start="", last_imported_end="", first_imported_start="", first_imported_end=""):
        '''
        :return: List of all records in onfloor table
        '''
        with connection.cursor() as cursor:
            query = f"SELECT * FROM onfloor"

            if (last_imported_start != None and len(last_imported_start) > 2) or (last_imported_end != None and len(last_imported_end) > 2):
                query += f" WHERE (DATE(last_imported) BETWEEN '{last_imported_start}' AND '{last_imported_end}')"

            if (first_imported_start != None and len(first_imported_start) > 2) or (last_imported_end != None and len(first_imported_end) > 2):
                query += f" WHERE (DATE(first_imported) BETWEEN '{first_imported_start}' AND '{first_imported_end}')"

            if (keyword != None and len(keyword) > 0):
                query += f" WHERE hawb LIKE '%{keyword}%'"

            result = query.split(" ")
            count = 0
            newresult = ""
            for i in result:
                if i == "WHERE":
                    if count > 0:
                        newresult += f" AND"
                    else:
                        newresult += f" {i}"
                    count += 1

                else:
                    newresult += f" {i}"
            if int(page) >= 0 and int(limit) >= 0:
                newresult += f" LIMIT {limit} OFFSET {page};"
            cursor.execute(newresult)
            results = cursor.fetchall()
            records = []
            for result in results:
                records.append(Record(
                    result[0],
                    result[1],
                    self.getFlags(result[2]),
                    result[3],
                    result[4],
                    result[5],
                    result[6],
                    result[7],
                    result[8],
                    result[9],
                    result[10],
                    result[11],
                    result[12],
                    result[13],
                    result[14],
                    result[15])
                )
            return records


class InRecords(models.Model):
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM onfloor_in")
            row = cursor.fetchall()
            return row

    def search(self, keyword):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM onfloor_in WHERE onfloor_in_hawb LIKE '%{keyword}%'")
            row = cursor.fetchall()
            return row

    class Meta:
        managed = False


class OutRecords(models.Model):
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM onfloor_out")
            row = cursor.fetchall()
            return row

    def search(self, keyword):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM onfloor_out WHERE onfloor_out_hawb LIKE '%{keyword}%'")
            row = cursor.fetchall()
            return row

    class Meta:
        managed = False


class SumRecords(models.Model):
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM onfloor_sum")
            row = cursor.fetchall()
            return row

    def search(self, keyword):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM onfloor_sum WHERE onfloor_sum_hawb LIKE '%{keyword}%'")
            row = cursor.fetchall()
            return row

    class Meta:
        managed = False


class ErrorRecords(models.Model):
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM errors")
            row = cursor.fetchall()
            return row

    def search(self, keyword):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM errors WHERE hawb LIKE '%{keyword}%'")
            row = cursor.fetchall()
            return row

    class Meta:
        managed = False
