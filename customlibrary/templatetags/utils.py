from django import template

register = template.Library()

def getattribute(value, args):
	# print("aaaa: : " + str(value) + " : " + str(args))
	if args in value:
		print("kommentar*******" + str(value[args]))
		return value[args]
register.filter('getattr', getattribute)

def get_from_model(value, args):
	# print("aaaa: : " + str(value) + " : " + str(args))
	return getattr(value, args)
register.filter('get_from_model', get_from_model)

def find_value_in_list(list_, value):
	for item in list_:
		if item == value:
			return value

def get_from_GET(value, args):
	value = {k: value.getlist(k) if len(value.getlist(k)) > 1 else v for k, v in value.items()}
	dict_ =  value.get(args)

	if not dict_:
		return ""
	return dict_
register.filter('get_from_GET', get_from_GET)

def get_q(request_GET):
	q = ""
	dict_ = {k: request_GET.getlist(k) if len(request_GET.getlist(k)) > 1 else v for k,v in request_GET.items() }
	for k, v in dict_.items():
		if len(v) < 1:
			q = q + k + "=" + v + "&"
		else:
			for item in v:
				q = q + k + "=" + item + "&"
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


def get_choices(choices):
	dict_ = {}
	for id, choice in choices:
		if id:
			dict_[id] = choice
	if bool(dict_):
		return dict_

	
register.filter('get_choices', get_choices)

@register.filter
def to_class_name(value):
    return value.__class__.__name__

