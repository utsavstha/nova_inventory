from django.shortcuts import render, redirect
from core.models import AuditRecords
import csv
from django.http import HttpResponse
import datetime
import numpy as np
import json
from django.core.files.storage import FileSystemStorage


def audit(request):
    columns = ["HAWB", "D", "O", "S", "V", "R", "C", "LAST IMPORTED", "FIRST IMPORTED", "FS DEVAN", "OF LOCATION",
               "OF DEVAN", "OF PC", "PC", "FS LOCATION", "FS PC", "FS PRIMARY", "CLIENT NAME", "RELEASE DATE", "CONSIGNEE"]
    audit = AuditRecords()

    if request.method == 'POST':
        page = request.POST.get('current_page')
        limit = request.POST.get('current_limit')
        searchKeyword = request.POST.get('tsearch')
        lStart = request.POST.get('lStart')
        lEnd = request.POST.get('lEnd')
        fStart = request.POST.get('fStart')
        fEnd = request.POST.get('fEnd')
        flag = request.POST.get('txt-flag')
        visibility = request.POST.get('columns_visibility')
        swapHistory = request.POST.get('swap_history')

        page = page if page != None else 0
        lStart = lStart if lStart != None else ''
        lEnd = lEnd if lEnd != None else ''
        fStart = fStart if fStart != None else ''
        fEnd = fEnd if fEnd != None else ''
        flag = flag if flag != None else 0
        swapHistory = json.loads(swapHistory) if swapHistory != None and len(
            swapHistory) > 0 else []

        records = audit.all(page=page, limit=limit, keyword=searchKeyword, last_imported_start=lStart,
                            last_imported_end=lEnd, first_imported_start=fStart, first_imported_end=fEnd)

        context = {"columns": columns, "swap_history": json.dumps([[0, 0]]), "columns_visibility": visibility, "txt-flag": flag, "current_page": page, "current_limit": limit, "search_data": searchKeyword,
                   "lStart": lStart, "lEnd": lEnd, "fStart": fStart, "fEnd": fEnd, "flag": flag, 'records': filterFlags(flag, records)}

        return render(request, 'audit/audit.html', context)
    else:
        columns_visibility = ["true" for i in range(len(columns))]

        context = {"columns": columns, "swap_history": json.dumps([[0, 0]]),
                   "current_page": 0, "current_limit": 50, "flag": 0, "columns_visibility": ','.join(map(str, columns_visibility)), 'records': audit.all(page=0, limit=50)}
        return render(request, 'audit/audit.html', context)

# def import_csv(request):
#     if request.method == 'POST':


def export_csv(request):
    if request.method == 'POST':
        searchKeyword = request.POST.get('tsearch')
        lStart = request.POST.get('lStart')
        lEnd = request.POST.get('lEnd')
        fStart = request.POST.get('fStart')
        fEnd = request.POST.get('fEnd')
        flag = request.POST.get('txt-flag')
        visibility = request.POST.get('columns_visibility')
        swapHistory = request.POST.get('swap_history')

        visibility = visibility.split(",") if visibility != None else []
        visibility = mapToBool(visibility)

        lStart = lStart if lStart != None else ''
        lEnd = lEnd if lEnd != None else ''
        fStart = fStart if fStart != None else ''
        fEnd = fEnd if fEnd != None else ''
        flag = flag if flag != None else 0

        swapHistory = json.loads(swapHistory) if swapHistory != None and len(
            swapHistory) > 0 else []

        audit = AuditRecords()

        entries = filterFlags(flag, audit.all(keyword=searchKeyword, last_imported_start=lStart,
                                              last_imported_end=lEnd, first_imported_start=fStart, first_imported_end=fEnd))
        swappedHeaders = swapEntries(["HAWB", "DUPLICATE", "OVERDUE", "SUM", "VER", "RELEASED", "ALL CLEAR", "LAST IMPORTED", "FIRST IMPORTED", "FS DEVAN", "OF LOCATION",
                                      "OF DEVAN", "OF PIECE COUNT", "PIECE COUNT DIFF", "FS LOCATION", "FS PIECE COUNT", "FS PRIMARY LOCATION", "CLIENT NAME", "RELEASE DATE", "CONSIGNEE"], swapHistory)
        visibility = swapEntries(visibility, swapHistory)

        filename = datetime.datetime.now().strftime("%Y%m%d") + ".csv"
        header = {'Content-Disposition': 'attachment; filename=""'}
        header['Content-Disposition'] = f'attachment; filename="{filename}"'
        response = HttpResponse(
            content_type='text/csv',
            headers=header,
        )
        row_list = [swappedHeaders]
        writer = csv.writer(response)

        for entry in entries:
            row_list.append(swapEntries([entry.hawb, entry.duplicate_flag, entry.overdue_flag, entry.total_sum_flag, entry.verified_flag, entry.released_flag, entry.all_clear_flag, entry.last_imported, entry.first_imported, entry.fs_devan,
                                         entry.of_location, entry.of_devan, entry.of_piece_count, entry.piece_count_difference, entry.fs_location, entry.fs_piece_count, entry.fs_primary_location, entry.client_name, entry.release_date, entry.consignee], swapHistory))

        writer.writerows(removeUnselectedColumns(row_list, visibility))

        return response


def swapEntries(inputEntry, swapHistory):
    entry = inputEntry
    for swaps in swapHistory:
        entry[swaps[0]], entry[swaps[1]] = entry[swaps[1]], entry[swaps[0]]
        print(swaps)

    return entry


def mapToBool(items):
    columns = []
    for item in items:
        if item == "true":
            columns.append(True)
        else:
            columns.append(False)
    return columns


def removeUnselectedColumns(entries, visibility):
    entries = np.array(entries)
    deletingColumns = []
    for i in range(len(visibility)):
        if visibility[i] != True:
            deletingColumns.append(i)

    return np.delete(entries, deletingColumns, axis=1)


def delcolumn(mat, i):
    return [row[:i] + row[i+1:] for row in mat]


def __removeUnselectedColumns(self, entries, selectedColumns):
    headers = self.__swapHeaders(["HAWB", "D", "O", "S", "V", "R", "C", "LAST IMPORTED", "FIRST IMPORTED", "FS DEVAN", "OF LOCATION",
                                  "OF DEVAN", "OF PC", "PC", "FS LOCATION", "FS PC", "FS PRIMARY", "CLIENT NAME", "RELEASE DATE", "CONSIGNEE"])
    newEntry = []

    for i in range(len(headers)):
        for j in range(len(selectedColumns)):
            if headers[i] == selectedColumns[j]:
                # print(f"index {i} Header {headers[i]} Selected {selectedRows[j]} Entry {entries[i]}")
                newEntry.append(entries[i])

    return newEntry


def filterFlags(flag, records):
    filtered = []
    flag = int(flag)
    if flag == 1:
        for record in records:
            if record.duplicate_flag:
                filtered.append(record)
        return filtered
    elif flag == 2:
        for record in records:
            if record.overdue_flag:
                filtered.append(record)
        return filtered
    elif flag == 3:
        for record in records:
            if record.total_sum_flag:
                filtered.append(record)
        return filtered
    elif flag == 4:
        for record in records:
            if record.verified_flag:
                filtered.append(record)
        return filtered
    elif flag == 5:
        for record in records:
            if record.released_flag:
                filtered.append(record)
        return filtered
    elif flag == 6:
        for record in records:
            if record.all_clear_flag:
                filtered.append(record)
        return filtered
    else:
        return records


def importFile(request):
    if request.method == 'POST':
        files = [request.FILES.get('file[%d]' % i)
                 for i in range(0, len(request.FILES))]
        # inputs obtained from form are grabbed here, similarly other data can be gathered
        abc = request.POST['abc']
        # location where you want to upload your files
        folder = 'my_folder'
        fs = FileSystemStorage(location=folder)
        for f in files:
            filename = fs.save(f.name, f)
    data = {'status': 'success'}
    response = json.dumps(data)
    return HttpResponse(response)
