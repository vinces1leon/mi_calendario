import re
from django.shortcuts import render
from django.http import JsonResponse
from .models import Persona, Actividad, Registro
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from openpyxl import Workbook
import datetime

def calendario(request):
    personas = Persona.objects.all()
    actividades = Actividad.objects.all()
    return render(request, 'eventos/calendario.html', {
        'personas': personas,
        'actividades': actividades
    })

def eventos_json(request):
    registros = Registro.objects.all()
    data = []

    return JsonResponse(data, safe=False)

@csrf_exempt
def agregar_persona(request):
    data = json.loads(request.body)
    nombre = data.get('nombre')
    if nombre:
        p, created = Persona.objects.get_or_create(nombre=nombre)
        return JsonResponse({'id': p.id, 'nombre': p.nombre, 'creado': created})
    return JsonResponse({'error': 'Nombre requerido'}, status=400)

@csrf_exempt
def eliminar_persona(request):
    data = json.loads(request.body)
    nombre = data.get('nombre')
    try:
        persona = Persona.objects.get(nombre=nombre)
        persona.delete()
        return JsonResponse({'status': 'ok'})
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Persona no encontrada'}, status=404)

@csrf_exempt
def registrar_actividad(request):
    data = json.loads(request.body)

    try:
        persona_id = data['persona']
        fecha = data['fecha']
        actividad_1 = data['actividad_1']
        horas_1 = data['horas_1']
        actividad_2 = data.get('actividad_2')
        horas_2 = data.get('horas_2')
        actividad_3 = data.get('actividad_3')
        horas_3 = data.get('horas_3')

        registro = Registro.objects.create(
            persona=Persona.objects.get(id=persona_id),
            fecha=fecha,
            actividad_1=Actividad.objects.get(id=actividad_1),
            horas_1=float(horas_1),
            actividad_2=Actividad.objects.get(id=actividad_2) if actividad_2 else None,
            horas_2=float(horas_2) if horas_2 else None,
            actividad_3=Actividad.objects.get(id=actividad_3) if actividad_3 else None,
            horas_3=float(horas_3) if horas_3 else None,
        )

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def natural_key(codigo):
    match = re.match(r"T(\d+)", codigo)
    return int(match.group(1)) if match else float('inf')

def resumen_registros(request, fecha):
    actividades = Actividad.objects.all()
    codigos = sorted(
        list({act.nombre.split(' - ')[0] for act in actividades}),
        key=natural_key
    )

    personas = Persona.objects.all().order_by('id')
    datos = []

    for idx, persona in enumerate(personas, 1):
        horas_por_codigo = defaultdict(float)
        registros = Registro.objects.filter(persona=persona, fecha=fecha)

        for reg in registros:
            if reg.actividad_1:
                codigo = reg.actividad_1.nombre.split(' - ')[0]
                horas_por_codigo[codigo] += reg.horas_1
            if reg.actividad_2:
                codigo = reg.actividad_2.nombre.split(' - ')[0]
                horas_por_codigo[codigo] += reg.horas_2 or 0
            if reg.actividad_3:
                codigo = reg.actividad_3.nombre.split(' - ')[0]
                horas_por_codigo[codigo] += reg.horas_3 or 0

        fila = {
            'numero': idx,
            'nombre': persona.nombre,
            'horas': [horas_por_codigo[c] if horas_por_codigo[c] != 0 else '' for c in codigos],
            'total': sum(horas_por_codigo.values())
        }
        datos.append(fila)

    return render(request, 'eventos/resumen.html', {
        'codigos': codigos,
        'datos': datos,
        'fecha': fecha
    })

@csrf_exempt
@require_POST
def deshacer_ultimo_registro(request):
    try:
        data = json.loads(request.body)
        persona_id = data.get('persona_id')
        fecha = data.get('fecha')

        if not persona_id or not fecha:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})

        try:
            persona = Persona.objects.get(id=persona_id)
        except Persona.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Persona con ID {persona_id} no existe'})

        registros = Registro.objects.filter(persona=persona, fecha=fecha).order_by('-id')
        if registros.exists():
            registros.first().delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': f'No hay registros para la persona "{persona.nombre}" en la fecha {fecha}'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def exportar_resumen_excel(request, fecha):
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()

    registros = Registro.objects.filter(fecha=fecha_dt)
    personas = Persona.objects.all()

    # Mostrar todas las actividades T1 a T24 (aunque no se hayan usado)
    codigos = [f"T{i}" for i in range(1, 25)]  # T1 hasta T24

    # Crear archivo Excel
    wb = Workbook()
    ws = wb.active
    ws.title = f"Resumen {fecha}"

    # Cabecera
    headers = ["Persona"] + codigos + ["Total"]
    ws.append(headers)

    for persona in personas:
        fila = [persona.nombre]
        resumen = {codigo: 0 for codigo in codigos}
        total_persona = 0

        registros_persona = registros.filter(persona=persona)

        for registro in registros_persona:
            actividades_y_horas = [
                (registro.actividad_1, registro.horas_1),
                (registro.actividad_2, registro.horas_2),
                (registro.actividad_3, registro.horas_3),
            ]
            for actividad, horas in actividades_y_horas:
                if actividad and horas:
                    codigo = actividad.nombre.split(" - ")[0]
                    if codigo in resumen:
                        resumen[codigo] += horas
                        total_persona += horas

        # Agrega valores, pero si es 0, deja vacío
        fila += [resumen[codigo] if resumen[codigo] != 0 else "" for codigo in codigos]
        fila.append(total_persona if total_persona != 0 else "")
        ws.append(fila)

    # Generar respuesta
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="resumen_{fecha}.xlsx"'
    wb.save(response)
    return response