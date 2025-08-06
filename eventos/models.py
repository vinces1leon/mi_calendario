from django.db import models

class Persona(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Actividad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Registro(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    fecha = models.DateField()
    actividad_1 = models.ForeignKey(Actividad, on_delete=models.SET_NULL, null=True, related_name='actividad1')
    horas_1 = models.FloatField()

    actividad_2 = models.ForeignKey(Actividad, on_delete=models.SET_NULL, null=True, blank=True, related_name='actividad2')
    horas_2 = models.FloatField(null=True, blank=True)

    actividad_3 = models.ForeignKey(Actividad, on_delete=models.SET_NULL, null=True, blank=True, related_name='actividad3')
    horas_3 = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.persona} - {self.fecha}"



