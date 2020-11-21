import datetime as dt

def year(request):

    date = dt.datetime.today().year
    return { 
        "year": date
    }
