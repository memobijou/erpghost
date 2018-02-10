from django import template

register = template.Library()


def getattribute(value, args):
    # print("aaaa: : " + str(value) + " : " + str(args))
    if args in value:
        print("kommentar*******" + str(value[args]))
        return value[args]


register.filter('getattr', getattribute)


def callattr(value, args):
    if args in value:
        print("CALLATTR*******" + str(value[args]()))
        return value[args]()


register.filter('callattr', callattr)


def get_from_model(value, arg):
    if hasattr(value, arg):
        return getattr(value, arg)


register.filter('get_from_model', get_from_model)


def find_value_in_list(list_, value):
    for item in list_:
        if item == value:
            return value


def get_from_GET(value, args):
    value = {k: value.getlist(k) if len(value.getlist(k)) > 1 else v for k, v in value.items()}
    dict_ = value.get(args)

    if not dict_:
        return ""
    return dict_


register.filter('get_from_GET', get_from_GET)


def get_q(request_GET):
    q = ""
    dict_ = {k: request_GET.getlist(k) if len(request_GET.getlist(k)) > 1 else v for k, v in request_GET.items()}
    for k, v in dict_.items():
        if len(v) < 1:
            q = q + k + "=" + v + "&"
        else:
            if not isinstance(v, str):
                for item in v:
                    q = q + k + "=" + item + "&"
            else:
                q = q + k + "=" + v + "&"

    q = q[:-1]
    return q


register.filter('get_q', get_q)


def remove_param_from_q(q, remove_value):
    print("!!!!!!!!: " + str(q))
    q = q.replace(remove_value, "")
    splitted_q = q.split("&")
    new_q = ""
    for string in splitted_q:
        if not "=" in string:
            continue
        elif "=" in string:
            if string[len(string) - 1] == "=":
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


def get_field_type(field):
    return field.__class__.__name__


register.filter('get_field_type', get_field_type)


@register.filter
def to_class_name(value):
    return value.__class__.__name__


def to_json(query_dict):
    meta = query_dict[0].__class__._meta
    field_names = meta.get_fields()
    result = []
    for q in query_dict:
        dict_ = {}
        for field in field_names:
            if hasattr(q, field.name):
                dict_[field.name] = getattr(q, field.name)
        if dict_:
            result.append(dict_)
    return result


register.filter('to_json', to_json)
