

from inputs.inputs import set_inputs

def test_set_inputs():
    inputs = ['https://www.fakedomain.com/' for _ in range(5)]
    i = set_inputs(inputs=inputs, url_col='url')
    assert isinstance(i, list) and isinstance(i[0], tuple)
    assert 'url' in i[0]._fields
    
    inputs = ['https://www.fakedomain.com/' for _ in range(5)]
    i = set_inputs(inputs=inputs, url_col='starting_url')
    assert isinstance(i, list) and isinstance(i[0], tuple)
    assert 'starting_url' in i[0]._fields
    assert i[0].starting_url == 'https://www.fakedomain.com/'
    
    inputs = [{'starting_url': 'https://www.fakedomain.com/', 'category': i} for i in ('x', 'y', 'z')]
    i = set_inputs(inputs=inputs, url_col='starting_url')
    assert isinstance(i, list) and len(i) > 0
    assert isinstance(i[0], tuple)
    assert 'starting_url' in i[0]._fields
    assert 'category' in i[0]._fields
    assert i[0].starting_url == 'https://www.fakedomain.com/'
    assert i[0].category == 'x' and i[1].category == 'y' and i[2].category == 'z'
    assert 'row' in type(i[0]).__name__
    
    inputs = 'https://www.fakedomain.com/'
    i = set_inputs(inputs=inputs, url_col='starting_url')
    assert isinstance(i, list) and len(i) > 0
    assert isinstance(i[0], tuple)
    
    i = set_inputs(inputs=inputs, url_col='url')
    assert isinstance(i, list) and len(i) > 0
    assert isinstance(i[0], tuple)
    assert i[0].url == 'https://www.fakedomain.com/'