I ended up implementing these ideas into [Confit](https://github.com/sampsyo/confit). See Confit issue [#2](https://github.com/sampsyo/confit/issues/2).

---

# pyConf
A module to simplify configuration of your Python program.

## Features
 - Elegant value accessing
 - Easily provide defaults
 - Template validation
 - Compatible with Python 2 and 3 (tested on CPython 2.7 and 3.3)

## Example Usage
```python
from pyconf import Config

cfg_dict = {1: {'lower': 'a'}}
defaults = {1: {'upper': 'A'}}
cfg = Config(cfg_dict, defaults)

assert(cfg._1.lower == 'a')
assert(cfg._1.upper is cfg['1']['upper'] == 'A')

template = {
    1: {
        'lower': str,
        'upper': {str, lambda x: x.isalpha()}  # == set([str, lambda x: x.isalpha()])
    }
}
assert(cfg.follows_template(template))
```
For more details see [`demo.py`](demo.py).

## Attribute naming
All config keys should be `str` or `int` instances.
Here's the algorithm turn any key, `key`, into a valid Python identifier:

 - If `key` is the empty string, the identifier is a single underscore (`_`)
 - Otherwise:
    - Make `key` a string
    - If `key`'s first character is a digit, add an underscore to the beginning
    - Replace characters from `string.punctuation` and `string.whitespace` with an underscore

This has the downside of causing collisions such as: `identifier('a b c') == identifier('a_b_c')`.<br>
If you can think of a better way to handle identifiers, tell me or provide a patch!


## Template Validation
```python
Config().follows_template(template, error_msgs={})
```
### Args
Name|Type|Content
:--:|:--:|:------
`template`|`dict`|Dictionary with configuration's expected structure containing checks.
`error_msgs`|`dict`<br>(optional)|Dictionary with configuration's expected structure that may contain both general and specific messages.

### Checks
A check can be one of the following:

 - a type
 - a callable returning a bool indicating if the given value is valid
 - a tuple of the form (callable, args, kwargs) where args can be omitted. The callable's first argument will always be the field's value.
 - a list of checks, where any one of them should validate
 - a set of checks that should all validate
 - a value

### Error Messages
`error_msgs` should have the same structure as the configuration, omitted items will be fetched from general errors.
General errors can be customized by defining the `_` key. These errors will be used in the section it is defined and it's children, but can be overridden in it's children by defining `_` once more.

`_`'s structure is the following:
```python
'_'  = {
  'invalid': 'used when the check failed',
  'missing': 'used when the element is missing',
  'prefix': 'a prefix for all errors',
  'suffix': 'a suffix for all errors'
}
```

Any number of these may be omitted, these (or the parent's
when applicable) general errors will be used:
```python
{
    'prefix': '{path}.{name} ',  # see the error formatting section below
    'invalid': 'is invalid',
    'missing': 'is missing',
    'suffix': '.'
}
```

You can also set invalid for a single element (including nested Config objects) by making it a string:
```python
{
  'element': 'used when the check failed'
}
```

### Error Formatting
The errors are formatted using `str.format` with these arguments:

Name|Content
:---:|:------
`path`|element's path in the configuration (relative to where `follows_template` was called)
`name`|element's name
`value`|element's value