#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 3.6
# @Filename:    test_agent.py
# @Author:      Samuel Hill
# @Date:        2020-02-10 15:39:38
# @Last Modified by:   Samuel Hill
# @Last Modified time: 2020-02-13 15:35:35

"""Simple example file for how to use Pythonian, and a test file to explore all
of the functionality Pythonian (and it's helpers) provide

Attributes:
    LOGGER (logging): The logger (from logging) to handle debugging
"""

from logging import getLogger, DEBUG, INFO
from time import sleep
from typing import Any
from companionsKQML import Pythonian, convert_to_boolean, convert_to_int

LOGGER = getLogger(__name__)


class TestAgent(Pythonian):
    """Pythonian agent specifically made to test functionality

    Attributes:
        name (str): This is the name your agent will register with
    """

    name = "TestAgent"

    def __init__(self, **kwargs):
        kwargs['debug'] = True  # you don't need this line in your agents
        super().__init__(**kwargs)
        if self.debug:
            LOGGER.setLevel(DEBUG)
        else:
            LOGGER.setLevel(INFO)

        # (test_ask_return_list1 ?_input ?return)
        self.add_ask(self.test_ask_return_list1)
        # (test_ask_return_list2 ?_input ?return1 ?return2)
        self.add_ask(self.test_ask_return_list2)
        # (test_ask_return_string ?_input ?return)
        self.add_ask(self.test_ask_return_string)
        # (test_ask_return_int ?_input ?return)
        self.add_ask(self.test_ask_return_int)
        # (test_ask_return_dict ?_input ?return)
        self.add_ask(self.test_ask_return_dict)

        self.add_achieve(self.test_achieve)
        self.add_achieve(self.test_achieve_return)
        self.add_achieve(self.test_convert_boolean)

        self.add_subscription('(test_junk_mail ?x)')

    @staticmethod
    def test_ask_return_list1(_input: Any):
        """Simple function to be called by ask-one queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            list: passes the input back along as a list to check the full input
                /output cycle in companions
        """
        LOGGER.debug('testing ask with _input %s', _input)
        return [_input]

    @staticmethod
    def test_ask_return_list2(_input: Any):
        """Simple function to be called by ask-one queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            list: passes the strings pass and test as a list to check the full
                input/output cycle in companions
        """
        LOGGER.debug('testing ask with _input %s', _input)
        return ["pass", "test"]

    @staticmethod
    def test_ask_return_string(_input: Any):
        """Simple function to be called by ask-one queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            list: passes the string pass to check the full input /output cycle
                in companions
        """
        LOGGER.debug('testing ask with _input %s', _input)
        return "pass"

    @staticmethod
    def test_ask_return_int(_input: Any):
        """Simple function to be called by ask-one queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            list: passes the string pass to check the full input /output cycle
                in companions
        """
        LOGGER.debug('testing ask with _input %s', _input)
        return 1

    @staticmethod
    def test_ask_return_dict(_input: Any):
        """Simple function to be called by ask-one queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            list: passes a populated dictionary to check the full input/output
                cycle in companions
        """
        LOGGER.debug('testing ask with _input %s', _input)
        return {'key1': ['a', 'b'], 'key2': 'c'}

    @staticmethod
    def test_achieve(_input: Any):
        """Simple function to be called by achieve queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions
        """
        LOGGER.debug('testing achieve with _input %s', _input)

    @staticmethod
    def test_achieve_return(_input: Any):
        """Simple function to be called by achieve queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            1, always a 1 for testing purposes
        """
        LOGGER.debug('testing achieve with _input %s', _input)
        return 1

    @staticmethod
    def test_convert_boolean(to_be_bool: Any):
        """Simple function to be called by achieve queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            bool: _input from companions converted to a boolean
        """
        LOGGER.debug('testing achieve with _input %s', to_be_bool)
        now_bool = convert_to_boolean(to_be_bool)
        LOGGER.debug('boolean conversion new value is %s', now_bool)
        return now_bool

    @staticmethod
    def test_convert_int(to_be_int: Any):
        """Simple function to be called by achieve queries by the same name

        Args:
            _input (Any): input to be passed to this function from companions

        Returns:
            int: _input from companions converted to a int
        """
        LOGGER.debug('testing achieve with _input %s', to_be_int)
        now_int = convert_to_int(to_be_int)
        LOGGER.debug('int conversion new value is %s', now_int)
        return now_int

    def more_junk_mail(self, data: Any):
        """Update the test_junk_mail subscription with the new data

        Args:
            data (Any): content of the junk mail to update the subscription
                with
        """
        LOGGER.debug('more junk mail has arrived %s', data)
        self.update_subscription('(test_junk_mail ?x)', data)

    def test_insert_to_companion(self, data: Any):
        """Insert the data into the session-reasoner (kb agent)

        Args:
            data (Any): fact to be inserted
        """
        LOGGER.debug('testing inserting data into Companion %s', data)
        self.insert_data(self, 'session-reasoner', data)


if __name__ == "__main__":
    AGENT = TestAgent.parse_command_line_args()
    # AGENT.test_insert_to_companion('(started TestAgent)')
    sleep(20)
    AGENT.more_junk_mail('Click here for...')
    sleep(10)
    AGENT.more_junk_mail('You have won! Just send your SSN to us and we will '
                         'send you the money')
