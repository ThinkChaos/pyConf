""" Simple demo showcasing what pyConf can do. """

from pyconf import Config

values = {
    1337: '1 M 50 1337',
    'A': {
        'ASCII': 65,
        'kind': 'alpha',
        'case': 'upper',
    },
    'a': {
        'ASCII': 97,
        'kind': 'alpha',
        # typo
        'case': 'lowre',
    },
    'B': {
        # additional zero
        'ASCII': 660,
        'kind': 'alpha',
        'case': 'upper',
    },
    'b': {
        # typo
        'ASCII': 89,
    },
    # the rest will come from the defaults
}

defaults = {
    'b': {
        # this will be overriden
        'ASCII': 98,
        'kind': 'alpha',
        'case': 'lower',
    },
}

template = {
    # type
    'A': {
        'ASCII': int,
        'kind': str,
        # either one
        'case': [str, bool],
    },
    # value
    'a': {
        'ASCII': 97,
        'kind': 'alpha',
        # either one
        'case': ['upper', 'lower'],
    },
    # function
    'B': {
        # args
        'ASCII': lambda x: 65 <= x <= 90,
        # args and kwargs
        'kind': (lambda x, *args, **kwargs: True, [0, 1], {'a': 'b'}),
        # kwargs
        'case': (lambda x, **kwargs: True, {'a': 'b'}),
    },
    # combinations
    'b': {
        # list (at least should be True)
        'ASCII': [bool, lambda x: 65 <= x <= 90],
        # set (all should be True)
        'kind': {str, lambda x: x.startswith('abc')},
    },
}

error_messages = {
    # general
    '_': {
        'prefix': '{path}.{name} ',
        'invalid': 'is invalid',
        'missing': 'is missing'
    },
    # case per case
    'a': {
        'case': {
            'invalid': 'should be "upper" or "lower"',
            'missing': 'is not defined'
        }
    },
    # local generals (replaces invalid and missing)
    'B': {
        '_': {
            'invalid': 'is not valid',
            'missing': 'is not defined'
        }
    },
    # local invalid
    'b': "ain't valid"
}

if __name__ == '__main__':
    cfg = Config(values, defaults)

    # accessing (nested) values
    assert(cfg.A.ASCII is cfg['A']['ASCII'])

    # overwritting (nested) values
    cfg.B.ASCII = 0
    assert(cfg.B.ASCII is cfg['B']['ASCII'])
    # This is overwritting only: if x.y wasn't defined it will be a standard
    # attribute which can't be accessed as x['y'].

    # correcting invalid identifiers
    assert(cfg._1337 is cfg['1337'])

    # defaults complete...
    assert(cfg.b.case == 'lower')

    # ...without overriding
    assert(cfg.b.ASCII == 89)

    # template validation
    assert(not cfg.follows_template(template, error_messages))
