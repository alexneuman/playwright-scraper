
from tool import Manager
from inputs.inputs import set_inputs

from pytest import fixture

@fixture
def manager():
    m = Manager(['https://www.fakedomain.com/' for _ in range(5)], url_col='url')
    return m

def test_manager_queue(manager):
    assert manager.queue.qsize() == 5
    