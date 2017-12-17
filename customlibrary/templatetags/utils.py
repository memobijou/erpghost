from django import template

register = template.Library()

def getattribute(value, args):
	return value[args]
register.filter('getattr', getattribute)

def get_from_GET(value, args):
	dict_ =  value.get(args)
	if not dict_:
		return ""
	return dict_
register.filter('get_from_GET', get_from_GET)

def get_q(request_GET):
	q = ""
	for k, v in request_GET.items():
		q = q + k + "=" + v + "&"
	q = q[:-1]
	return q
register.filter('get_q', get_q)

def remove_param_from_q(q, remove_value):
	q = q.replace(remove_value, "")
	splitted_q = q.split("&")
	new_q = ""
	for string in splitted_q:
		if not "=" in string:
			continue
		elif "=" in string:
			if string[len(string)-1] == "=":
				continue
			elif string[0] == "=":
				continue
			else:
				new_q = new_q + string + "&"
		else:
			new_q = new_q + string + "&"
	new_q = new_q[:-1]
	return new_q
register.filter('remove_param_from_q', remove_param_from_q)

