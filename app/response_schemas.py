_FORMATS = ('linkedin', 'email', 'article', 'ad')
_NON_AD_FORMATS = ('linkedin', 'email', 'article')
_AD_VARIANTS = ('A', 'B', 'C')
_CATEGORIES = ('unsupported_fact', 'contradiction', 'repetition', 'tone', 'format')


def _invalid():
    raise ValueError('invalid input')


def _string_list(value, limit, item_limit=None):
    if not isinstance(value, list) or not value or len(value) > limit:
        _invalid()
    seen = set()
    for item in value:
        if not isinstance(item, str) or not item or item in seen:
            _invalid()
        if item_limit is not None and len(item) > item_limit:
            _invalid()
        seen.add(item)
    return list(value)


def _requested_formats(value):
    formats = _string_list(value, 4)
    for fmt in formats:
        if fmt not in _FORMATS:
            _invalid()
    return formats


def _chunk_ids(value):
    return _string_list(value, 16, 512)


def _piece_keys(value):
    keys = _string_list(value, 6)
    for key in keys:
        base, separator, variant = key.partition(':')
        if not separator:
            _invalid()
        if base == 'ad':
            if variant not in _AD_VARIANTS:
                _invalid()
        elif base in _NON_AD_FORMATS:
            if variant != '':
                _invalid()
        else:
            _invalid()
    return keys


def _object(properties):
    return {
        'type': 'object',
        'properties': properties,
        'required': list(properties),
        'additionalProperties': False,
    }


def _questions_schema():
    return {
        'type': 'array',
        'minItems': 0,
        'maxItems': 5,
        'items': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 500,
        },
    }


def generation_schema(formats: list[str], chunk_ids: list[str]) -> dict:
    requested = _requested_formats(formats)
    citations = _chunk_ids(chunk_ids)
    has_ad = 'ad' in requested
    max_pieces = sum(1 for item in requested if item != 'ad')
    if has_ad:
        max_pieces += 3

    piece_properties = {
        'format': {
            'type': 'string',
            'enum': list(requested),
        },
        'variant': {
            'type': 'string',
            'enum': ['', 'A', 'B', 'C'] if has_ad else [''],
        },
        'body': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 4000,
        },
        'citations': {
            'type': 'array',
            'minItems': 1,
            'maxItems': 8,
            'items': {
                'type': 'string',
                'enum': list(citations),
            },
        },
    }

    properties = {
        'status': {
            'type': 'string',
            'enum': ['draft', 'needs_input'],
        },
        'questions': _questions_schema(),
        'pieces': {
            'type': 'array',
            'minItems': 0,
            'maxItems': max_pieces,
            'items': _object(piece_properties),
        },
    }
    return _object(properties)


def review_schema(piece_keys: list[str], chunk_ids: list[str]) -> dict:
    keys = _piece_keys(piece_keys)
    citations = _chunk_ids(chunk_ids)

    issue_properties = {
        'piece_key': {
            'type': 'string',
            'enum': ['all'] + list(keys),
        },
        'category': {
            'type': 'string',
            'enum': list(_CATEGORIES),
        },
        'message': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 500,
        },
        'citations': {
            'type': 'array',
            'minItems': 0,
            'maxItems': 8,
            'items': {
                'type': 'string',
                'enum': list(citations),
            },
        },
    }

    properties = {
        'verdict': {
            'type': 'string',
            'enum': ['pass', 'revise', 'needs_input'],
        },
        'issues': {
            'type': 'array',
            'minItems': 0,
            'maxItems': 12,
            'items': _object(issue_properties),
        },
        'questions': _questions_schema(),
    }
    return _object(properties)
