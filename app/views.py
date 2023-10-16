
from django.shortcuts import render
from django.db import connection
from . import models



# def GetPhenoms(request):
#     #global phenoms
#     return render(request, 'phenoms.html', {'data' : models.Phenomens.objects.values('phenom_id', 'phenom_name', 'image')})

def GetPhenom(request, id):
    #global phenoms
    return render(request, 'phenom.html', {'data' : models.Phenomens.objects.filter(phenom_id=id).first()})

def StatusIsDel(id):
    try:
        with connection.cursor() as cursor:
            query = f"UPDATE phenomens SET status = 'Удален' WHERE phenom_id = %s"
            cursor.execute(query, [id])
            connection.commit()
            return True
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return False
        
def GetPhenoms(request):
    answer = []
    input_phenom = request.GET.get('value')
    #меняем статус на удален если нажата кнопка
    phenom_del_id = request.GET.get('phenom_id')
    if (phenom_del_id):
        StatusIsDel(phenom_del_id)
    #если значение поиска передано, то делаем поиск через ORM 
    if (input_phenom):
        phenom = models.Phenomens.objects.exclude(status='Удален').filter(field_name=input_phenom)
        answer.append(phenom)
    else:
    #если поле пусто, просто сохраняем все явления
        phenoms = models.Phenomens.objects.exclude(status='Удален')
        answer = [i for i in phenoms]
        input_phenom = ''
    return render(request, 'phenoms.html', {'data' : answer, 'search_value': input_phenom})