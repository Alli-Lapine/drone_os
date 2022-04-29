import pytest
from unittest.mock import AsyncMock, ANY
from util.storage import Storage, RegisteredDrone, DroneChannel
from util import load_codes, load_hives, load_filters


@pytest.fixture
def filterplugin():
    bot = AsyncMock()
    bot.logger = AsyncMock()
    load_codes()
    load_hives()
    load_filters()
    from cogs.filter import Filter

    return Filter(bot=bot)


@pytest.fixture
def hook():
    hook = AsyncMock(name="webhook")
    hook.send = AsyncMock(name="webhook_send")
    return hook


@pytest.fixture
def msg():
    msg = AsyncMock(name="Message")
    msg.delete = AsyncMock(name="delete")
    msg.channel = AsyncMock(name="channel")
    msg.channel.id = 100000000000000001
    return msg


@pytest.fixture
def normaldrone():
    drone1 = RegisteredDrone(
        {"discordid": 100000000000000001, "droneid": "TSTN", "hive": "lapine/unaffiliated"}
    )
    Storage.backend.save(drone1)
    yield 100000000000000001
    Storage.backend.delete(drone1)


@pytest.fixture
def enforcedrone():
    drone1 = RegisteredDrone(
        {
            "discordid": 100000000000000041,
            "droneid": "TSTE",
            "config": {"enforce": True},
            "hive": "lapine/unaffiliated",
        }
    )
    Storage.backend.save(drone1)
    yield 100000000000000041
    Storage.backend.delete(drone1)


@pytest.fixture
def enforcedronechan():
    chan = DroneChannel({"discordid": 100000000000000001, "config": {"enforcedrones": True}})
    Storage.backend.save(chan)
    yield 100000000000000001
    Storage.backend.delete(chan)


@pytest.fixture
def enforceallchan():
    chan = DroneChannel({"discordid": 100000000000000004, "config": {"enforceall": True}})
    Storage.backend.save(chan)
    yield 100000000000000004
    Storage.backend.delete(chan)


@pytest.mark.asyncio
class TestFilterLogic:
    async def test_sends_normal_msg(self, filterplugin, hook, msg, normaldrone):
        msg.configure_mock(content="TSTN :: Y helo thar")
        msg.author.id = normaldrone
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_called_with(
            username=ANY, content="TSTN :: ☼ :: Y helo thar", avatar_url=ANY, embed=ANY
        )
        msg.delete.assert_called()

    async def test_ignores_normies_without_chanenforce(self, filterplugin, hook, msg):
        msg.configure_mock(content="Y helo thar")
        msg.author.id = 100000000000000999
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_not_called()

    async def test_deletes_wrong_prefix(self, filterplugin, hook, msg, normaldrone):
        msg.configure_mock(content="1234 :: Y helo thar")
        msg.author.id = normaldrone
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_called()

    async def test_deletes_unprefixed_from_drone_in_droneenforce(
        self, filterplugin, hook, msg, enforcedrone
    ):
        msg.configure_mock(content="Y helo thar")
        msg.author.id = enforcedrone
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_called()

    async def test_sends_in_droneenforce(self, filterplugin, hook, msg, enforcedrone):
        msg.configure_mock(content="TSTE :: Y helo thar")
        msg.author.id = enforcedrone
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_called_with(
            username=ANY, content="TSTE :: ☼ :: Y helo thar", avatar_url=ANY, embed=ANY
        )
        msg.delete.assert_called()

    async def test_sends_in_chanenforce(
        self, filterplugin, hook, msg, normaldrone, enforcedronechan
    ):
        msg.configure_mock(content="TSTN :: Y helo thar")
        msg.author.id = normaldrone
        msg.channel.id = enforcedronechan
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_called_with(
            username=ANY, content="TSTN :: ☼ :: Y helo thar", avatar_url=ANY, embed=ANY
        )
        msg.delete.assert_called()

    async def test_deletes_unprefixed_from_drone_in_chanenforce(
        self, filterplugin, hook, msg, normaldrone, enforcedronechan
    ):
        msg.configure_mock(content="Y helo thar")
        msg.author.id = normaldrone
        msg.channel.id = enforcedronechan
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_called()

    async def test_ignores_normies_in_chanenforce(self, filterplugin, hook, msg, enforcedronechan):
        msg.configure_mock(content="Y helo thar")
        msg.author.id = 100000000000000999
        msg.channel.id = enforcedronechan
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_not_called()

    async def test_deletes_unprefixed_from_drone_in_chanenforceall(
        self, filterplugin, hook, msg, normaldrone, enforceallchan
    ):
        msg.configure_mock(content="Y helo thar")
        msg.author.id = normaldrone
        msg.channel.id = enforceallchan
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_called()

    async def test_deletes_unprefixed_from_normie_in_chanenforceall(
        self, filterplugin, hook, msg, enforceallchan
    ):
        msg.configure_mock(content="Y helo thar")
        msg.author.id = 100000000000000999
        msg.channel.id = enforceallchan
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_not_called()
        msg.delete.assert_called()

    async def test_sends_in_chanenforceall(
        self, filterplugin, hook, msg, normaldrone, enforceallchan
    ):
        msg.configure_mock(content="TSTN :: Y helo thar")
        msg.author.id = normaldrone
        msg.channel.id = enforceallchan
        await filterplugin.drone_filter_handler(msg, hook)
        hook.send.assert_called_with(
            username=ANY, content="TSTN :: ☼ :: Y helo thar", avatar_url=ANY, embed=ANY
        )
        msg.delete.assert_called()
