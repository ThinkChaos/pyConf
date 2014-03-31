""" A module to simplify configuration of your program. """

from string import punctuation, whitespace

try:
    from string import maketrans
except ImportError:
    maketrans = str.maketrans


trans_table = maketrans(
    punctuation + whitespace,
    '_' * (len(punctuation) + len(whitespace))
)


def identifier(name):
    """ Return valid identifier for str/int. """
    if name == '':
        return '_'

    name = str(name)

    if name[0].isdigit():
        name = '_' + name

    return name.translate(trans_table)


class Config(dict):

    """ An object designed to simplify configuration. """

    general_errors = {
        'prefix': '{path}.{name} ',
        'invalid': 'is invalid',
        'missing': 'is missing',
        'suffix': '.'
    }

    def __init__(self, values={}, defaults={}):
        self.update(values)
        self.set_defaults(defaults)

    def __getitem__(self, key):
        try:
            return super(Config, self).__getitem__(key)
        except KeyError:
            pass

        try:
            return super(Config, self).__getitem__(identifier(key))
        except KeyError:
            pass

        raise KeyError(key)

    def __getattr__(self, attr):
        try:
            # If Python doesn't find an attr, we get it from the dict
            return self[attr]
        except KeyError:
            pass

        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if attr in self:
            self[attr] = value
        else:
            super(Config, self).__setattr__(attr, value)

    def update(self, values):
        """ Insert values into the Config object.

        This also replaces nested dicts with Config instances.


        Note:
          This method will only working with dict subclasses.
        """
        for k, v in values.items():
            if isinstance(k, (str, int)):
                if isinstance(v, dict):
                    # Nested dicts become Configs
                    super(Config, self).update({identifier(k): Config(v)})
                else:
                    super(Config, self).update({identifier(k): v})
            else:
                # Don't let key be anything else than str/int as they'll also
                # be accessed as attrs
                raise TypeError(k)

        # maybe be useful for one-liners
        return self

    def set_defaults(self, defaults):
        """ Like `update` but only adds undefined keys. """
        for k, v in defaults.items():
            if isinstance(k, (str, int)):
                k = identifier(k)
                if isinstance(v, dict):
                    # Don't entirely overwrite nested Configs
                    if not k in self:
                        self.update({k: Config(v)})
                    else:
                        self[k].set_defaults(v)
                elif not k in self:
                    self.update({k: v})
            else:
                raise TypeError(k)

        return self

    def on_error(self, error, **kwargs):
        """ Tell the user there's an error in the configuration.

        This method is called when a certain field failed it's check during a
        `follows_template` test.


        Args:
          prefix (str): Error message prefix as defined in error_msgs (dict
            passed to `follows_template`).
          error (str): Error message from error_msgs.
          suffix (str): Error message suffix as defined in error_msgs.
          missing (bool, optional): Whether the error was caused by a missing
            configuration field.
          kwargs (dict): Catches information used to format the error.


        Note:
          See `follows_template` for more information on the error_msgs dict.
        """
        print(error.format(**kwargs))

    def follows_template(self, template, error_msgs={}):
        """ Return True if the configuration follows the given template.

        Args:
          template (dict): Dictionary with configuration's expected structure
            containing checks. For more details see the ``Checks`` section.
          error_msgs (dict, optional): Dictionary with configuration's
            expected structure containing messages to associate with
            configured values.


        Checks:
          A check can be one of the following:
            - a type
            - a callable returning a bool indicating if the given value is
              valid
            - a tuple of the form (callable, args, kwargs) where args can be
              omitted. The callable's first argument will always be the field's
              value.
            - a list of checks, where any one of them should validate
            - a set of checks that should all validate
            - a value


        Error Formatting:
          The errors are formatted using `str.format` with these arguments:
            path: element's path in the configuration (relative to where
                `follows_template` was called)
            name: element's name
            value: element's value


        Error Messages:
          error_msgs should have the same structure as the configuration,
          omitted items will be fetched from general errors.
          General errors can be customized by defining the _ key. These
          errors will be used in the section it is defined and it's children,
          but can be overridden in it's children by defining _ once more.

          _'s structure is the following:
          '_'  = {
            'invalid': 'used when the check failed',
            'missing': 'used when the element is missing',
            'prefix': 'a prefix for both invalid and missing',
            'suffix': 'a suffix for both invalid and missing'
          }

          Any number of these may be omitted, these (or the parent's
          when applicable) general errors will be used:
          {
              'prefix': '{path}.{name} ',
              'invalid': 'is invalid',
              'missing': 'is missing',
              'suffix': '.'
          }

          You can also set invalid for a single element (including nested
          Config objects) by making it a string:
          {
            'elem': 'used when the check failed'
          }
        """
        return self._follows_template(
            template,
            self._prepare_error_msgs(error_msgs)
        )

    def _check(self, attr, check):
        """ Perform the checks. """
        if isinstance(check, list):
            # Check per check instead of all([check results]) to be efficient
            for c in check:
                if self._check(attr, c):
                    return True

            return False

        if isinstance(check, set):
            # Same reasoning as above, this also allows assumptions:
            # {str, lambda attr: attr.startswith('a')} won't throw an
            # AttributeError when attr is not a str
            for c in check:
                if not self._check(attr, c):
                    return False

            return True

        if isinstance(check, type):
            return isinstance(attr, check)

        if callable(check):
            return check(attr)

        if isinstance(check, tuple):
            check = dict(enumerate(check))

            func, args, kwargs = (
                check.get(0, lambda x: False),
                check.get(1, []),
                check.get(2, {}),
            )

            if not kwargs and isinstance(args, dict):
                args, kwargs = [], args

            return func(attr, *args, **kwargs)

        # resort to value comparison
        return attr == check

    def _get_error_msg(self, attr_name, error_msgs, missing=False):
        situation = 'missing' if missing else 'invalid'
        default = error_msgs._.get(situation)

        error = error_msgs.get(attr_name, default)

        if isinstance(error, Config):
            error = (
                error.get('prefix', error_msgs._.prefix)
                + error.get(situation, default)
                + error.get('suffix', error_msgs._.suffix)
            )
        else:
            error = error_msgs._.prefix + error + error_msgs._.suffix

        return error

    def _prepare_error_msgs(self, error_msgs, defaults={}):
        """ Help propagate general errors and keep local ones. """
        if isinstance(error_msgs, str):
            error_msgs = Config({'_': {'invalid': error_msgs}})

        return Config(error_msgs, Config(defaults, {'_': self.general_errors}))

    def _follows_template(self, template, error_msgs={}, path=''):
        res = True

        formatting_info = {
            'missing': True,
            'name': None,
            'path': path,
            'value': None,
        }

        for attr_name, check in template.items():
            formatting_info['name'] = attr_name

            try:
                attr = getattr(self, identifier(attr_name))
            except AttributeError:
                res = False
                self.on_error(
                    self._get_error_msg(attr_name, error_msgs, missing=True),
                    **formatting_info
                )
                continue

            if isinstance(check, dict):
                if not isinstance(attr, Config):
                    res = False
                    self.on_error(
                        self._get_error_msg(
                            attr_name,
                            error_msgs,
                            missing=True
                        ),
                        **formatting_info
                    )
                    continue

                if not attr._follows_template(
                    check,
                    self._prepare_error_msgs(
                        error_msgs.get(attr_name, {}),
                        {'_': error_msgs._}
                    ),
                    (path + '.' if path else '') + str(attr_name)
                ):
                    res = False

            else:
                if not self._check(attr, check):
                    res = False
                    formatting_info.update({'missing': False, 'value': attr})
                    self.on_error(
                        self._get_error_msg(
                            attr_name,
                            error_msgs,
                            missing=False
                        ),
                        **formatting_info
                    )

        return res
