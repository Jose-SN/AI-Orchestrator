"""DI container unit tests."""

from app.bootstrap.container import AppContainer


def test_container_wires_services(container: AppContainer):
    chat = container.chat_service()
    permissions = container.permission_service()
    assert chat is not None
    assert permissions is not None


def test_container_singleton_within_instance(container: AppContainer):
    assert container.chat_service() is container.chat_service()
