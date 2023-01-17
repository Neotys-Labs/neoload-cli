from neoload_cli_lib import config_global

__prefix = "$hooks"


def trig(name, *args, **kwargs):
    functions_to_trig = config_global.get_attr(__prefix + "." + name)
    if functions_to_trig:
        for function_to_trig in functions_to_trig:
            split = function_to_trig.split('.')
            module_str = split[0]
            module = __import__(module_str)
            for comp in split[1:]:
                module_str = module_str + '.' + comp
                module2 = getattr(module, comp, None)
                if module2 is None:
                    __import__(module_str)
                    module2 = getattr(module, comp)
                module = module2
            module(*args, **kwargs)


def register(name, function):
    hook = config_global.get_attr(__prefix + "." + name)
    hook_set = set(hook) if hook else set()

    hook_set.add(function)
    config_global.set_attr(__prefix + "." + name, list(hook_set))


def unregister(name, function):
    hook = config_global.get_attr("$hooks." + name)
    if hook:
        hook.remove(function)
        if hook:
            config_global.set_attr("$hooks." + name, list(hook))
        else:
            config_global.set_attr(__prefix + "." + name, None)


def is_registered(name, function):
    hook = config_global.get_attr(__prefix + "." + name)
    return hook and function in hook
