from django.shortcuts import render, redirect
from core.models import ErrorRecords
# Create your views here.


def errorRecord(request):
    records = ErrorRecords()
    if request.method == 'POST':
        searchKeyword = request.POST.get('search')
        if len(searchKeyword) > 0:
            context = {"records": records.search(
                searchKeyword), "search_data": searchKeyword}
        else:
            context = {"records": records.all()}
        return render(request, 'errorRecord/errorrecords.html', context)

    else:
        context = {"records": records.all()}
        return render(request, 'errorRecord/errorrecords.html', context)
