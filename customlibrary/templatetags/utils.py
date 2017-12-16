from django import template

register = template.Library()

def getattribute(value, args):
	return value[args]
register.filter('getattr', getattribute)