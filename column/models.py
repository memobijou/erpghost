from django.db import models
#from position.models import Position

class Column(models.Model):
	volumen = models.FloatField(null=False, blank=True, default="100.0")
	#positions = models.ManyToManyField(Position,through="ColumnPosition")

	def __str__(self):
		return str(self.id)+ "/" + str(self.volumen)

# class ColumnPosition(models.Model):
#     positions = models.ForeignKey(Position, on_delete=models.CASCADE)
#     columns = models.ForeignKey(Column, on_delete=models.CASCADE, unique=False, blank=False, null=False)

#     def __str__(self):
#     	return str(self.columns.id) + " : " + str(self.positions)