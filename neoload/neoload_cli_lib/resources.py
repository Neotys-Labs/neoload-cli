import logging


def get_resource_as_string(namespace, file):
    try:
        import importlib.resources as pkg_resources
    except ImportError:
        # Try backported to PY<37 `importlib_resources`.
        import importlib_resources as pkg_resources

    logging.debug({'namespace': namespace, 'file': file})
    if hasattr(pkg_resources, 'files'):  # files is present from Python 3.9
        return pkg_resources.files(namespace).joinpath(file).read_text(encoding='utf-8')
    return pkg_resources.read_text(namespace, file, encoding='utf-8')
