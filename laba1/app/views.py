from django.http import HttpResponse
from django.shortcuts import render
from datetime import date

phenoms = [
            {'title': 'Дождь', 'id': 1, 'image': 'rain.jpg', 'unit': 'мм', 'description': 'Атмосферные осадки, выпадающие из облаков в виде капель жидкости со средним диаметром от 0,5 до 6-7 мм'},
            {'title': 'Снег', 'id': 2, 'image': 'snow.jpg', 'unit': 'мм', 'description': 'Форма атмосферных осадков, состоящая из мелких кристаллов льда'},
            {'title': 'Град', 'id': 3, 'image': 'hail.jpg', 'unit': 'мм', 'description': 'Вид ливневых осадков в виде частиц льда округлой формы размером от миллиметра до нескольких сантиметров'},
            {'title': 'Ветер', 'id': 4, 'image': 'wind.jpg', 'unit': 'м/с', 'description': 'Поток воздуха, который движется около земной поверхности'},
            {'title': 'Мороз', 'id': 5, 'image': 'freeze.jpg', 'unit': 'градусы Цельсия', 'description': 'Температурное состояние, при котором градусник показывает ниже нуля'},
            {'title': 'Жара', 'id': 6, 'image': 'sun.jpg', 'unit': 'градусы Цельсия', 'description': 'Состояние атмосферы в данной области, характеризующееся горячим, нагретым солнечными лучами воздухом'},
            {'title': 'Туман', 'id': 7, 'image': 'fog.jpg', 'unit': 'видимость в метрах', 'description': 'Скопление воды в воздухе, образованное мельчайшими частичками воды'},
        ]

def hello(request):
    return render(request, 'index.html', {
        'current_date': date.today()
    })

# def GetPhenoms(request):
#     global phenoms
#     return render(request, 'phenoms.html', {'data' : phenoms})

def GetPhenom(request, id):
    global phenoms
    return render(request, 'phenom.html', {'data' : phenoms[id-1]})

def GetPhenoms(request):
     global phenoms
     answer = []
     input_phenom = request.GET.get('value')
     if (input_phenom):
        for i in phenoms:
            if (input_phenom == i['title']):
                answer.append(i.copy())
     else:
        answer = phenoms
        input_phenom = ''
     return render(request, 'phenoms.html', {'data' : answer, 'search_value': input_phenom})