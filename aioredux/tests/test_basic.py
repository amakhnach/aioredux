import asyncio
from unittest import mock

import toolz

import aioredux
from aioredux.tests import base

try:
    from types import coroutine
except ImportError:
    from asyncio import coroutine


def add_todo(text):
    return {'type': 'ADD_TODO', 'text': text}


def reducer(state, action):
    if action['type'] == 'ADD_TODO':
        todos = state['todos'] + (action['text'],)
        return toolz.assoc(state, 'todos', todos)
    return state


class TestBasic(base.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        super().setUp()
        self.initial_state = {
            'todos': (),
        }

    def tearDown(self):
        self.loop.close()
        self.loop = None
        super().tearDown()

    def test_todo(self):

        @coroutine
        def go():
            store = yield from aioredux.create_store(lambda state, action: state, self.initial_state, loop=self.loop)
            self.assertIsNotNone(store)
            self.assertIsNotNone(store.state)

        self.loop.run_until_complete(go())

    def test_todo_reducer(self):

        @coroutine
        def go():
            store = yield from aioredux.create_store(reducer, self.initial_state, loop=self.loop)
            self.assertIsNotNone(store.state)
            self.assertIsNotNone(store.state['todos'])
            self.assertEqual(len(store.state['todos']), 0)
            yield from store.dispatch(add_todo('todo text'))
            self.assertIsNotNone(store.state)
            self.assertIsNotNone(store.state['todos'])
            self.assertEqual(len(store.state['todos']), 1)

        self.loop.run_until_complete(go())

    def test_subscribe(self):

        @coroutine
        def go():
            store = yield from aioredux.create_store(lambda state, action: state, self.initial_state, loop=self.loop)
            self.assertEqual(len(store.listeners), 0)
            unsubscribe = store.subscribe(lambda: None)
            self.assertEqual(len(store.listeners), 1)
            unsubscribe()
            self.assertEqual(len(store.listeners), 0)

        self.loop.run_until_complete(go())

    def test_listener_execution(self):
        @coroutine
        def go():
            store = yield from aioredux.create_store(reducer, self.initial_state, loop=self.loop)
            mock_listener = mock.MagicMock()
            unsubscribe = store.subscribe(mock_listener)
            yield from store.dispatch(add_todo('todo text'))
            self.assertTrue(mock_listener.called)
            unsubscribe()

        self.loop.run_until_complete(go())

    def test_coroutine_listener_execution(self):
        mock_listener = mock.MagicMock()

        @coroutine
        def foo():
            mock_listener()

        @coroutine
        def go():
            store = yield from aioredux.create_store(reducer, self.initial_state, loop=self.loop)

            unsubscribe = store.subscribe(foo)
            yield from store.dispatch(add_todo('todo text'))
            self.assertTrue(mock_listener.called)
            unsubscribe()

        self.loop.run_until_complete(go())

    def test_coroutine_magic_method_listener_execution(self):
        mock_listener = mock.MagicMock()

        class Foo:
            @coroutine
            def __call__(self, *args, **kwargs):
                mock_listener()

        @coroutine
        def go():
            store = yield from aioredux.create_store(reducer, self.initial_state, loop=self.loop)

            unsubscribe = store.subscribe(Foo())
            yield from store.dispatch(add_todo('todo text'))
            self.assertTrue(mock_listener.called)
            unsubscribe()

        self.loop.run_until_complete(go())
