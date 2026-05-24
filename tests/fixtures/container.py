import pytest

from app.bootstrap.container import AppContainer, reset_container


@pytest.fixture(autouse=True)
def _reset_di_container():
    reset_container()
    yield
    reset_container()


@pytest.fixture
def container() -> AppContainer:
    return AppContainer()
