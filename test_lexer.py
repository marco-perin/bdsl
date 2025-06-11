import lexer as lx


def test_comment():
    """Test regex for commment"""

    (tok_type, *rest) = lx.get_token_type(';;')
    print(tok_type)
    print(rest)
    assert tok_type == lx.TOKEN_COMMENT
    assert len(rest) == 1
    assert rest[0] == ''

    (tok_type, *rest) = lx.get_token_type(';; TEST COMMENT')
    print(tok_type)
    print(rest)
    assert tok_type == lx.TOKEN_COMMENT
    assert len(rest) == 1
    assert rest[0] == 'TEST COMMENT'


def test_function():
    """Test function syntax recognition"""

    line = 'fn function_name()'

    toks = line.split(' ')

    (tok_type, *_) = lx.get_token_type(toks[0])
    assert tok_type == lx.TOKEN_FN_DEF, f'got {lx.token_names[tok_type]}'
    # assert len(rest) == 1
    # assert rest[0] == ''

    line = 'fn function_name(x,y)'
