from django.shortcuts import render, redirect
from core.models import OutRecords
# Create your views here.


def outRecord(request):
    records = OutRecords()
    if request.method == 'POST':
        searchKeyword = request.POST.get('search')
        if len(searchKeyword) > 0:
            context = {"records": records.search(
                searchKeyword), "search_data": searchKeyword}
        else:
            context = {"records": records.all()}
        return render(request, 'outRecord/outrecords.html', context)

    else:
        context = {"records": records.all()}
        return render(request, 'outRecord/outrecords.html', context)
