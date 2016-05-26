from functools import wraps

from flask import current_app


def state_or_409(volume, state):
    def decorator(f):
        decorator.__name__ = f.__name__
        decorator.__doc__ = f.__doc__

        @wraps(f)
        def conflict():
            return {'message': 'Resource not in state: {}'.format(state)}, 404

        if volume.unpacked_value.get('state') != state:
            return conflict

        @wraps(f)
        def ok(*args, **kwargs):
            return f(*args, **kwargs)
        return ok
    return decorator


def get_volume_or_404(manager, volume_id='0'):
    def decorator(f):
        decorator.__name__ = f.__name__
        decorator.__doc__ = f.__doc__

        @wraps(f)
        def not_found():
            return {'message': 'Not Found'}, 404

        volume = manager.by_id(volume_id)
        if volume is None:
            return not_found

        @wraps(f)
        def found(*args, **kwargs):
            kwargs['volume'] = volume
            return f(*args, **kwargs)
        return found
    return decorator


def inject_var(key, value):
    def decorator(f):
        decorator.__name__ = f.__name__
        decorator.__doc__ = f.__doc__

        @wraps(f)
        def inner_dec(*args, **kwargs):
            kwargs[key] = value
            return f(*args, **kwargs)
        return inner_dec
    return decorator


def inject_volume_manager(f):
    @wraps(f)
    def inner_dec(*args, **kwargs):
        kwargs['volume_manager'] = current_app.volume_manager
        return f(*args, **kwargs)
    return inner_dec
