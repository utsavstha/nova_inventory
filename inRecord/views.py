from django.shortcuts import render, redirect
from core.models import InRecords
# Create your views here.


def inRecord(request):
    records = InRecords()
    if request.method == 'POST':
        searchKeyword = request.POST.get('search')
        if len(searchKeyword) > 0:
            context = {"records": records.search(
                searchKeyword), "search_data": searchKeyword}
        else:
            context = {"records": records.all()}
        return render(request, 'inRecord/inrecords.html', context)

    else:
        context = {"records": records.all()}
        return render(request, 'inRecord/inrecords.html', context)
