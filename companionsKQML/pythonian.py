#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 3.6
# @Filename:    pythonian.py
# @Author:      Samuel Hill
# @Date:        2020-02-10 16:10:26
# @Last Modified by:   Samuel Hill
# @Last Modified time: 2020-03-02 16:02:12

"""Pythonian agent, sits on top of the modified KQMLModule -
CompanionsKQMLModule. Uses subscription management classes to allow for cleaner
subscription polling and updating.

Attributes:
    LOGGER (logging): The logger (from logging) to handle debugging
"""

from inspect import getfullargspec
from logging import getLogger, DEBUG, INFO
from threading import Thread
from time import sleep
from traceback import print_exc
from typing import Any, Callable
from kqml import KQMLPerformative, KQMLList
from .companionsKQMLModule import CompanionsKQMLModule, listify, performative

LOGGER = getLogger(__name__)


###############################################################################
#                    Python Outsourced Predicate Module                       #
###############################################################################

class Pythonian(CompanionsKQMLModule):
    """Outsourced predicate layer for Python, allows for easy creation of ask
    queries, subscribable

    Attributes:
        achieves (dict): dictionary of functions to call on achieve of a given
            name. Usually the function name is the name used in the achieve
            queries but the name can be anything that you specify when adding
            the achieve.
        asks (dict): dictionary of functions to call on ask of a given
            name. Usually the function name is the name used in the ask
            queries but the name can be anything that you specify when adding
            the ask.
        name (str): This is the name your agent will register with
        poller (Thread): thread that controls polling for updates to the
            subscriptions and dispatches those updates accordingly
        polling_interval (int): the interval at which the polling thread will
            check for new data
        subscriptions (SubscriptionManager): customized dictionary of patterns
            with the associated data and subscribers.
    """

    name = "Pythonian"

    def __init__(self, **kwargs):
        self.achieves = {}
        self.asks = {}
        self.subscriptions = SubscriptionManager()
        self.polling_interval = 1
        self.poller = Thread(target=self._poll_for_subscription_updates,
                             args=[])
        LOGGER.info('Starting subcription poller...')
        self.poller.start()
        super().__init__(**kwargs)
        if self.debug:
            LOGGER.setLevel(DEBUG)
        else:
            LOGGER.setLevel(INFO)

    ###########################################################################
    #                              Tell Function                              #
    ###########################################################################

    def receive_tell(self, msg: KQMLPerformative, content: KQMLList):
        """Override default KQMLModule tell to simply log the content and reply
        with nothing

        Arguments:
            msg (KQMLPerformative): overall message to be passed along in reply
            content (KQMLList): tell content from companions to be logged
        """
        LOGGER.debug('received tell: %s', content)
        reply_msg = performative(f'(tell :sender {self.name} :content :ok)')
        self.reply(msg, reply_msg)

    ###########################################################################
    #                            Ask-one Functions                            #
    ###########################################################################

    def add_ask(self, func: Callable[..., Any], name: str = None):
        """Adds the given function (func) to the dictionary of asks under the
        key of the given name. If subscribable is true then we also add the
        pattern to our subscription dictionary and advertise it.

        Arguments:
            func (Callable[..., Any]): function to be called on ask query
            name (str, optional): name to pair to this function for query calls

        Raises:
            ValueError: func must be a callable function
        """
        if not callable(func):
            raise ValueError('func must be a callable function')
        if name is not None:
            if not isinstance(name, str):
                raise ValueError('name must be a string')
            self.asks[name] = func
        else:
            self.asks[func.__name__] = func

    def receive_ask_one(self, msg: KQMLPerformative, content: KQMLList):
        """Override of default ask one, creates Companions style responses.
        Gets the arguments bindings from the cdr of the content. The predicate
        (car) is then used to find the function bound to the ask predicate, and
        that function is called with the bounded argument list unpacked into
        it's own inputs. The resulting query is then passed along to the
        _response_to_query helper which will properly respond to patterns or
        bindings based on out response type.

        Arguments:
            msg (KQMLPerformative): reply mechanism
            content (KQMLList): predicate to look up in asks dict, arguments of
                the ask call - to be passed in to the call.

        Returns:
            None: returns only to exit function early if conditions aren't met
        """
        if content.head() not in self.asks:
            error_msg = f'No ask query predicate named {content.head()} known'
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        bounded = []
        for each in content.data[1:]:
            if str(each[0]) != '?':
                bounded.append(each)
        ask_question = self.asks[content.head()]
        expected_args = len(getfullargspec(ask_question).args)
        if expected_args != len(bounded):
            error_msg = (f'Expected {expected_args} input arguments to query '
                         f'predicate {content.head()}, got {len(bounded)}')
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        LOGGER.info('received ask-one %s', content.head())
        try:
            results = self.asks[content.head()](*bounded)
        except (TypeError, ValueError) as except_msg:
            LOGGER.debug('Failed execution: %s, %s', except_msg, print_exc())
            error_msg = f'An error occurred while executing: {content.head()}'
            self.error_reply(msg, error_msg)
            return
        LOGGER.debug('Ask-one returned results: %s', results)
        self._response_to_query(msg, content, results, msg.get('response'))

    ###########################################################################
    #                            Achieve Functions                            #
    ###########################################################################

    def achieve_on_agent(self, receiver: str, data: Any):
        """Sends a KQML achieve to the receiver with the data input as a list.

        Arguments:
            receiver (str): name of the receiving agent
            data (Any): content to send along with achieve
        """
        msg = performative(f'(achieve :sender {self.name} :receiver {receiver}'
                           f' :content {listify(data)})')
        # TODO: Do we want to listify the data for an achieve or rely on
        # proper formatting?
        self.send(msg)

    def add_achieve(self, func: Callable[..., Any], name: str = None):
        """Adds the given function (func) to the dictionary of achieves under
        the key of the given name. If no name is given (which is the default)
        the function name is used.

        Arguments:
            func (Callable[..., Any]): function to call on achieve of this
                function (with given name or - if not given - function name)
            name (str, optional): name of function to look for on achieve,
                defaults to function.__name__ (key in achieves dictionary)
        """
        if not callable(func):
            raise ValueError('func must be a callable function')
        if name is not None:
            if not isinstance(name, str):
                raise ValueError('name must be a string')
            self.achieves[name] = func
        else:
            self.achieves[func.__name__] = func

    def receive_achieve(self, msg: KQMLPerformative, content: KQMLList):
        """Overrides the default KQMLModule receive for achieves and instead
        does basic error checking before attempting the action by calling the
        proper ask function with the arguments passed along as inputs.

        Arguments:
            msg (KQMLPerformative): predicate/ signifier of task (message
                sent to python from companions)
            content (KQMLList): action task is referring to (content of
                message)

        Returns:
            None: returns only to exit function early if conditions aren't met
        """
        if content.head() != 'task':
            error_msg = (f'Only support achieve command of task, instead got '
                         f'{content.head()}')
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        action = content.get('action')
        if not action:
            error_msg = 'No action for achieve task provided'
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        if action.head() not in self.achieves:
            error_msg = f'No action named {action.head()} is known'
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        achieve_question = self.achieves[action.head()]
        expected_args = len(getfullargspec(achieve_question).args)
        actual_args = action.data[1:]
        if expected_args != len(actual_args):
            error_msg = (f'Expected {expected_args} input arguments to achieve'
                         f' task {action.head()}, got {len(actual_args)}')
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        LOGGER.info('received achieve %s', action.head())
        try:
            results = self.achieves[action.head()](*actual_args)
        except (TypeError, ValueError) as except_msg:
            LOGGER.debug('Failed execution: %s, %s', except_msg, print_exc())
            error_msg = f'An error occurred while executing {action.head()}'
            self.error_reply(msg, error_msg)
            return
        LOGGER.debug('Acheive returned results: %s', results)
        reply = performative(f'(tell :sender {self.name} :content '
                             f'{listify(results)})')
        self.reply(msg, reply)

    ###########################################################################
    #                          Subscription Functions                         #
    ###########################################################################

    # CURRENTLY UNUSED... Can we even receive plain old ask-alls?
    def advertise(self, pattern: str):
        """Sends an advertise message for an ask-all command with the content
        set to the input pattern

        Arguments:
            pattern (str): content to be advertised as an ask-all
        """
        reply_id = f'id{self.reply_id_counter}'
        self.reply_id_counter += 1
        msg = performative(f'(advertise :sender {self.name} :receiver '
                           f'facilitator :reply-with {reply_id} :content '
                           f'(ask-all :receiver {self.name} :in-reply-to '
                           f'{reply_id} :content {pattern}))')
        self.send(msg)

    def advertise_subscribe(self, pattern: str):
        """Sends an advertise message for an subscribe to an ask-all command
        with the content set to the input pattern

        Arguments:
            pattern (str): content to be advertised as a subscription to an
                ask-all
        """
        reply_id = f'id{self.reply_id_counter}'
        self.reply_id_counter += 1
        msg = performative(f'(advertise :sender {self.name} :receiver '
                           f'facilitator :reply-with {reply_id} :content '
                           f'(subscribe :receiver {self.name} :in-reply-to '
                           f'{reply_id} :content (ask-all :receiver '
                           f'{self.name} :in-reply-to {reply_id} :content '
                           f'{pattern})))')
        self.send(msg)

    def add_subscription(self, pattern: str):
        """Parses pattern for a function and (unless one is given) uses that
        as the underlying ask function (stored by add_ask). Advertises the
        pattern as subscribable.

        Args:
            pattern (str): pattern to send a subscription out on

        Raises:
            TypeError: pattern must be of type string
            ValueError: pattern must have at least one predicate in it and be
                surrounded by parentheses
        """
        if not isinstance(pattern, str):
            raise TypeError('pattern must be of type str')
        if not pattern.startswith('(') or not pattern.endswith(')'):
            raise ValueError('pattern must start and end with parenthesis')
        if pattern.strip('()').split() == []:
            raise ValueError('pattern must contain at least a predicate')
        self.subscriptions.add_new_subscription(pattern)
        self.advertise_subscribe(pattern)
        self.num_subs += 1

    def update_subscription(self, pattern: str, *args: Any):
        """Looks to see if the arguments to pattern have changes since last
        time, if so it will update those arguments in the subscription manager.

        Arguments:
            pattern (str): string representing the pattern (id of subscription)
            *args (Any): data associated with the pattern (either to be bound
                or, by default used in a substitution pattern). For conveneince
                you can enter each variable to be bound as a positional
                argument and this will gather them up.
        """
        self.subscriptions.update(pattern, args)

    def receive_subscribe(self, msg: KQMLPerformative, content: KQMLList):
        """Override of KQMLModule default, expects a performative of ask-all.
        Gets the ask-all query from the message contents, then checks
        to see if the query head is in the dictionary of available asks and
        checks if the query string is in the dictionary of subscribers. If both
        of these are true we then append the message to the subscriber query,
        clean out any previous subscription data, and reply with a tell ok
        message.

        Arguments:
            msg (KQMLPerformative): performative to be passed along to reply
                and stored in the subscribers dictionary (for future replies)
            content (KQMLList): ask-all for a query

        Returns:
            None: returns only to exit function early if conditions aren't met
        """
        if content.head() != 'ask-all':
            error_msg = (f'Only supports ask-all subscription, received '
                         f'unsupported performative {content.head()}')
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        query = content.get('content')
        pattern = query.to_string()
        if query.head() not in self.asks:
            error_msg = f'No ask named {query.head()} is known'
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        if pattern not in self.subscriptions:
            error_msg = f'Ask ({query.head()}) is not subscribable'
            LOGGER.debug(error_msg)
            self.error_reply(msg, error_msg)
            return
        LOGGER.info('received subscription %s to %s', msg, pattern)
        self.subscriptions.subscribe(pattern, msg)
        reply_msg = f'(tell :sender {self.name} :content :ok)'
        self.reply(msg, performative(reply_msg))

    def _poll_for_subscription_updates(self):
        """Goes through the subscription updates as they come in and properly
        respond to the query."""
        while self.ready:
            for _, subscription in self.subscriptions.items():
                if subscription.new_data is not None:
                    LOGGER.info('updating subscriptions for %s', subscription)
                    for subscriber in subscription:
                        ask = subscriber.get('content')
                        query = ask.get('content')
                        self._response_to_query(subscriber, query,
                                                subscription.new_data,
                                                ask.get('response'))
                    subscription.retire_data()
            sleep(self.polling_interval)

    ###########################################################################
    #                             Insert Functions                            #
    ###########################################################################

    def insert_data(self, receiver: str, data: Any, wm_only: bool = False):
        """Takes the data input by the user and processes it into an insert
        message which is subsequently sent off to Companions.

        Arguments:
            receiver (str): name of the receiver (agent with a kb to insert to)
            data (Any): fact to insert (data to be listify'd)
            wm_only (bool, optional): whether or not this should only be
                inserted into the working memory (default: False)
        """
        msg = performative(f'(insert :sender {self.name} :receiver {receiver} '
                           f':wm-only? {"t" if wm_only else "nil"} :content '
                           f'{data})')
        self.send(msg)

    def insert_to_microtheory(self, receiver: str, data: Any, mt_name: str,
                              wm_only: bool = False):
        """Inserts a fact into the given microtheory using ist-Information

        Arguments:
            receiver (str): name of the receiver (agent with a kb to insert to)
            data (Any): fact to insert
            mt_name (str): microtheory name
            wm_only (bool, optional): whether or not this should only be
                inserted into the working memory (default: False)
        """
        new_data = f'(ist-Information {mt_name} {data})'
        self.insert_data(receiver, new_data, wm_only)

    def insert_microtheory(self, receiver: str, data_list: list, mt_name: str,
                           wm_only: bool = False):
        """Inserts a list of facts into the given microtheory

        Arguments:
            receiver (str): name of the receiver (agent with a kb to insert to)
            data_list (list): list of facts to insert (list with each elemenet
                having data to be listify'd)
            mt_name (str): microtheory name
            wm_only (bool, optional): whether or not this should only be
                inserted into the working memory (default: False)
        """
        for data in data_list:
            self.insert_to_microtheory(receiver, data, mt_name, wm_only)


###############################################################################
#                         Subscription Management                             #
###############################################################################

class SubscriptionManager(dict):
    """Extention of dict for handling regular subscription operations"""

    def add_new_subscription(self, pattern: str):
        """Adds a new Subscription object as the value to a key of pattern

        Args:
            pattern (str): query pattern associated with this subscription
        """
        self[pattern] = Subscription()

    def subscribe(self, pattern: str, subscriber: KQMLPerformative):
        """Add a subscriber to the specified subscription

        Args:
            pattern (str): query pattern associated with a subscription
            subscriber (KQMLPerformative): msg sent to subscribe an agent
                so that when new data is polled the subscribers can simply
                be replied to
        """
        self[pattern].subscribe(subscriber)

    def update(self, pattern: str, data: Any):
        """Updates the data associated with a subscription

        Args:
            pattern (str): query pattern associated with a subscription
            data (Any): data to update the pattern with
        """
        self[pattern].update(data)

    def retire_data(self, pattern: str):
        """Retires the data associated with a subscription

        Args:
            pattern (str): query pattern associated with a subscription
        """
        self[pattern].retire_data()


class Subscription():
    """A simple class to handle subscriptions to a pattern, and updating the
    data associated with it.

    Attributes:
        new_data (Any): new data to be used in updating the subscription query
            pattern (passed along to _response_to_query).
        old_data (Any): copy of the new data after it has been retired, used
            for only updating new if it differs from the last value.
        subscribers (list): list of subscription messages to reply to when
            there is new data
    """

    def __init__(self):
        self.subscribers = []
        self.new_data = None
        self.old_data = None

    def __len__(self):
        return len(self.subscribers)

    def __getitem__(self, subscriber_number: int):
        return self.subscribers[subscriber_number]

    def __str__(self):
        return (f'Subscribers: {self.subscribers}, New data: {self.new_data},'
                f' Old data: {self.old_data}')

    def subscribe(self, subscriber: KQMLPerformative):
        """Adds a subscriber to the list of subscribers.

        Args:
            subscriber (KQMLPerformative): msg sent to subscribe an agent
                so that when new data is polled the subscribers can simply
                be replied to
        """
        self.subscribers.append(subscriber)

    def update(self, data: Any):
        """Checks that this is indeed an update (not the same as the previous
        data), and if so set the new_data to the input data

        Args:
            data (Any): new data to be used in updating the subscription query
                pattern (passed along to _response_to_query)
        """
        if self.old_data != data:
            self.new_data = data

    def retire_data(self):
        """Cycles new_data to old_data and resets new_data"""
        self.old_data = self.new_data
        self.new_data = None


###############################################################################
#                             Running Pythonian                               #
###############################################################################

def test(test_input: Any):
    """test function for simple Pythonian test for achieve

    Arguments:
        test_input (Any): thing to be printed

    Returns:
        1, always 1. For testing purposes.
    """
    print(str(test_input))
    return 1


if __name__ == "__main__":
    AGENT = Pythonian.parse_command_line_args()
    AGENT.add_achieve(test)
