from django.shortcuts import render, redirect
from core.models import SumRecords
# Create your views here.


def sumRecord(request):
    records = SumRecords()
    if request.method == 'POST':
        searchKeyword = request.POST.get('search')
        if len(searchKeyword) > 0:
            context = {"records": records.search(
                searchKeyword), "search_data": searchKeyword}
        else:
            context = {"records": records.all()}
        return render(request, 'sumRecord/sumrecords.html', context)

    else:
        context = {"records": records.all()}
        return render(request, 'outRecord/outrecords.html', context)
