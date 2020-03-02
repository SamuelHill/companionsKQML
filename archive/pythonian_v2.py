#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 3.6
# @Filename:    pythonian.py
# @Date:        2018-11-08 15:25:41
# @Last Modified by:   Samuel Hill
# @Last Modified time: 2020-03-01 06:11:42

"""
Wrapper class around the KQML module to allow for easy integration of python
code with Common Lisp - specifically Companions. This integration is
accomplished by message passing through KQML messages that can both send and
receive data from a Companions agent.
"""

import io
import socket
import threading
import time
import traceback
import logging
import concurrent.futures
from datetime import datetime
from kqml import KQMLModule, KQMLReader, KQMLPerformative, KQMLList, \
    KQMLDispatcher, KQMLToken, KQMLString

LOGGER = logging.getLogger('Pythonian')
LOGGER.setLevel(logging.DEBUG)


# pylint: disable=too-many-instance-attributes
#   There are 15+ attributes given to us by KQMLModule, and we add an
# additional 13. Only 6 of the default attributes are used in here; name, host,
# port, reply_id_counter, out, and dispatcher. name is set to Pythonian as the
# default for this class; host, port, out, and dispatcher all use the defaults
# from KQMLModule currently. Those 6 attributes are necessary and the remaining
# attributes we have could be consolidated in various ways:
#   - The dictionaries of asks, achieves, and subscriptions could themselves be
#   put in a dictionary of registered functions or something.
#   - Create separate classes to handle the Threading or storage capabilities
# However all of that is unnecessary as 7 is far to low of a bound and for this
# project the ~19 used attributes are all distinct enough as to be warranted.
class Pythonian(KQMLModule):
    """Wrapper around the KQMLModule to create a simple Companions integration.

    KQML gives us default communications protocols that we have altered to fit
    both Lisp standards and Companion expectations. In addition, we have added
    some functions that interface with Companions both by exposing the
    Companions style communication functions and by adding helpful generic
    wrappers around those functions to make integrating even more simple.

    Extends:
        KQMLModule

    Variables:
        name {str} -- The name of the agent to register with
    """

    name = "Pythonian"

    def __init__(self, **kwargs):
        # Call the parent class' constructor which sends a registration
        # message, setting the agent's name to be recognized by the
        # Facilitator.
        if 'localPort' in kwargs:  # keyword is camelCase but,
            self.local_port = kwargs['localPort']  # variable is snake_case
            del kwargs['localPort']
        else:
            self.local_port = 8950
        if 'port' in kwargs:
            port = kwargs['port']
            del kwargs['port']
        else:
            port = 9000

        super(Pythonian, self).__init__(name=self.name, port=port, **kwargs)
        self.starttime = datetime.now()
        # tracking functions related to asks and achieves
        self.achieves = {}
        self.asks = {}
        # subscription stuff
        self.subscribers = {}  # query:[subscribe,msgs]
        self.subcribe_data_old = {}
        self.subcribe_data_new = {}
        self.polling_interval = 1
        self.poller = threading.Thread(
            target=self._poll_for_subscription_updates, args=[])
        # Finally, start the listener for incoming messages
        self.listen_socket = socket.socket()
        self.listen_socket.bind(('', self.local_port))
        self.listen_socket.listen(10)
        self.listener = threading.Thread(target=self._listen, args=[])
        # ready to go
        self.state = 'idle'
        self.ready = True
        self.poller.start()
        self.listener.start()

    ###########################################################################
    #                            Utility functions                            #
    ###########################################################################

    def add_achieve(self, name, func):
        """Adds the given function (func) to the dictionary of achieves under
        the key of the given name.

        Arguments:
            name {str} -- key in achieves dictionary
            func {function} -- value paired to key, function to be called on
                               achieve (with given name)
        """
        self.achieves[name] = func

    def achieve_on_agent(self, receiver, data):
        """Sends a KQML message to the proper receiver with the data formatted
        properly as a list.

        Arguments:
            receiver {str} -- name of the receiver
            data {[type]} -- anything
        """
        msg = KQMLPerformative('achieve')
        msg.set('sender', self.name)
        msg.set('receiver', receiver)
        msg.set('content', listify(data))
        # pylint: disable=no-member
        # pylint was unable to pick up on the host and port variables being in
        # a defaults dict which is then used to do __setattr__ with the key
        # value pairs from the dict.
        self.connect(self.host, self.port)
        self.send(msg)
        # TODO - Does this need to close after?
        # self._close_socket()

    def add_ask(self, name, func, pattern, subscribable=False):
        """Adds the given function (func) to the dictionary of asks under the
        key of the given name. If subscribable is true then we also add the
        pattern to our subscription dictionary and advertise it.

        Arguments:
            name {str} -- key in asks dictionary
            func {function} -- value paired to key, function to be called on
                               ask
            pattern {str} -- name of subscribers

        Keyword Arguments:
            subscribable {bool} -- [description] (default: {False})
        """
        self.asks[name] = func
        if subscribable:
            self.subscribers[pattern] = []
            self.advertise_subscribe(pattern)

    def advertise(self, pattern):
        """Connects to the host, then builds and sends a message to the
        facilitator with the pattern input as the content, then closes the
        connection.

        Arguments:
            pattern {[type]} -- content to be sent
        """
        # pylint: disable=no-member
        # pylint was unable to pick up on the host and port variables being in
        # a defaults dict which is then used to do __setattr__ with the key
        # value pairs from the dict.
        self.connect(self.host, self.port)
        reply_id = f'id{self.reply_id_counter}'
        self.reply_id_counter += 1
        content = KQMLPerformative('ask-all')
        content.set('receiver', self.name)
        content.set('in-reply-to', reply_id)
        content.set('content', pattern)
        msg = KQMLPerformative('advertise')
        msg.set('sender', self.name)
        msg.set('receiver', 'facilitator')
        msg.set('reply-with', reply_id)
        msg.set('content', content)
        self.send(msg)
        self._close_socket()

    def advertise_subscribe(self, pattern):
        """Connects to the host, then builds and sends a message to the
        facilitator with the pattern input as the content, then closes the
        connection.

        Arguments:
            pattern {[type]} -- content to be sent
        """
        # pylint: disable=no-member
        # pylint was unable to pick up on the host and port variables being in
        # a defaults dict which is then used to do __setattr__ with the key
        # value pairs from the dict.
        self.connect(self.host, self.port)
        reply_id = f'id{self.reply_id_counter}'
        self.reply_id_counter += 1
        content = KQMLPerformative('ask-all')
        content.set('receiver', self.name)
        content.set('in-reply-to', reply_id)
        content.set('content', pattern)
        subscribe = KQMLPerformative('subscribe')
        subscribe.set('receiver', self.name)
        subscribe.set('in-reply-to', reply_id)
        subscribe.set('content', content)
        msg = KQMLPerformative('advertise')
        msg.set('sender', self.name)
        msg.set('receiver', 'facilitator')
        msg.set('reply-with', reply_id)
        msg.set('content', subscribe)
        self.send(msg)
        self._close_socket()

    def update_query(self, query, *args):
        """Looks to see if the arguments to query have changes since last time,
        if so it will update those arguments in the subscribe_data_new dict.

        Arguments:
            query {[type]} -- string representing the query
            *args {[type]} -- anything you would input into the query
        """
        if query in self.subcribe_data_old:
            if self.subcribe_data_old[query] != args:
                LOGGER.debug("Updating %s with %s", query, args)
                self.subcribe_data_new[query] = args

    # TODO: ADD CHECK FOR RECEIVER BEING OF SIMPLE AGENT TYPE, NOT FACILITATOR
    def insert_data(self, receiver, data, wm_only=False):
        """Takes the data input by the user and processes it into an insert
        message which is subsequently sent off to Companions.

        Arguments:
            receiver {str} -- name of the receiver
            data {[type]} -- anything that can be listified

        Keyword Arguments:
            wm_only {bool} -- whether or not this should only be inserted into
                              the working memory (default: {False})
        """
        msg = KQMLPerformative('insert')
        msg.set('sender', self.name)
        msg.set('receiver', receiver)
        if wm_only:
            msg.append(':wm-only?')
        msg.set('content', listify(data))
        # pylint: disable=no-member
        # pylint was unable to pick up on the host and port variables being in
        # a defaults dict which is then used to do __setattr__ with the key
        # value pairs from the dict.
        self.connect(self.host, self.port)
        self.send(msg)
        # TODO - Does this need to close after?
        # self._close_socket()

    def insert_to_microtheory(self, receiver, data, mt_name, wm_only=False):
        """Inserts a fact into the given microtheory using ist-Information

        Arguments:
            receiver {str} -- passed through to insert data
            data {[type]} -- anything that can be listified, the fact to insert
            mt_name {str} -- microtheory name

        Keyword Arguments:
            wm_only {bool} -- whether or not this fact should go to working
                              memory only or just the KB (default: {False})
        """
        new_data = '(ist-Information {} {})'.format(mt_name, data)
        self.insert_data(receiver, new_data, wm_only)

    def insert_microtheory(self, receiver, data_list, mt_name, wm_only=False):
        """Inserts a list of facts into the given microtheory

        Arguments:
            receiver {str} -- passed through to insert data
            data_list {list} -- list of facts to be added, facts can be
                                anything you can listify.
            mt_name {str} -- microtheory name

        Keyword Arguments:
            wm_only {bool} -- whether or not this fact should go to working
                              memory only or just the KB (default: {False})
        """
        for data in data_list:
            self.insert_to_microtheory(receiver, data, mt_name, wm_only)

    ###########################################################################
    #                                Overrides                                #
    ###########################################################################

    def register(self):
        """Overrides the KQMLModule default and uses Companions standards to
        send proper registration.
        """
        if self.name is not None:
            perf = KQMLPerformative('register')
            perf.set('sender', self.name)
            perf.set('receiver', 'facilitator')
            # pylint: disable=no-member
            # pylint was unable to pick up on the host variable being in a
            # defaults dict which is then used to do __setattr__ with the key
            # value pairs from the dict.
            socket_url = f'"socket://{self.host}:{self.local_port}"'
            content = KQMLList([socket_url, 'nil', 'nil', self.local_port])
            perf.set('content', content)
            self.send(perf)

    def receive_eof(self):
        """Override of the KQMLModule default which exits on eof, we instead
        just pass and do nothing on end of file.
        """
        # pylint: disable=unnecessary-pass
        # When there are no comments in this function (document string
        # included) this method passes the unnecessary-pass but fails on the
        # missing-docstring. This is a pylint bug.
        pass

    def receive_ask_one(self, msg, content):
        """Override of default ask one, creates Companions style responses.

        Gets the arguments bindings from the cdr of the content. The predicate
        (car) is then used to find the function bound to the ask predicate, and
        that function is called with the bounded argument list unpacked into
        it's own inputs. The resulting query is then passed along to the
        _response_to_query helper which will properly respond to patterns or
        bindings based on out response type.

        Arguments:
            msg {KQMLPerformative} -- pred and response type
            content {KQMLPerformative} -- arguments of the ask, passed to pred
        """
        bounded = []
        for each in content.data[1:]:
            if str(each[0]) != '?':
                bounded.append(each)
        results = self.asks[content.head()](*bounded)
        print(results)
        self._response_to_query(msg, content, results, msg.get('response'))

    def receive_achieve(self, msg, content):
        """Overrides the default KQMLModule receive for achieves and instead
        does basic error checking before attempting the action by calling the
        proper ask function with the arguments passed along as inputs.

        Arguments:
            msg {KQMLPerformative} -- predicate/ signifier of task
            content {KQMLPerformative} -- action task is referring to
        """
        if content.head() == 'task':
            action = content.get('action')
            if action:
                if action.head() in self.achieves:
                    try:
                        args = action.data[1:]
                        results = self.achieves[action.head()](*args)
                        LOGGER.debug("Return of achieve: %s", results)
                        reply = KQMLPerformative('tell')
                        reply.set('sender', self.name)
                        reply.set('content', listify(results))
                        self.reply(msg, reply)
                    # pylint: disable=broad-except
                    # The above try can throw KQMLBadPerformativeException,
                    # KQMLException, ValueError, and StopWaitingSignal at the
                    # least. To stay simple and more in-line with PEP8 we are
                    # logging the traceback and the user should be made aware
                    # of the fact that an error occurred via the error_reply.
                    # For these reasons the 'broad-except' is valid here.
                    except Exception:
                        LOGGER.debug(traceback.print_exc())
                        error_msg = 'An error occurred while executing: '
                        self.error_reply(msg, error_msg + action.head())
                else:
                    self.error_reply(msg, 'Unknown action: ' + action.head())
            else:
                self.error_reply(msg, 'No action for achieve task provided')
        else:
            error_msg = 'Unexpected achieve command: '
            self.error_reply(msg, error_msg + content.head())

    def receive_tell(self, msg, content):
        """Override default KQMLModule tell to simply log the content and reply
        with nothing

        Arguments:
            msg {KQMLPerformative} -- tell to be passed along in reply
            content {KQMLPerformative} -- tell from companions to be logged
        """
        LOGGER.debug('received tell: %s', content)  # lazy logging
        reply_msg = KQMLPerformative('tell')
        reply_msg.set('sender', self.name)
        reply_msg.set('content', None)
        self.reply(msg, reply_msg)

    def receive_subscribe(self, msg, content):
        """Override of KQMLModule default, expects a performative of ask-all.

        Gets the ask-all query from the message contents (the contents of
        the content variable is the query that we care about), then checks
        to see if the query head is in the dictionary of available asks and
        checks if the query string is in the dictionary of subscribers. If both
        of these are true we then append the message to the subscriber query,
        clean out any previous subscription data, and reply with a tell ok
        message.

        Arguments:
            msg {KQMLPerformative} -- performative to be passed along in reply
                                      and stored in the subscribers dictionary
            content {KQMLPerformative} -- ask-all for a query
        """
        LOGGER.debug('received subscribe: %s', content)  # lazy logging
        if content.head() == 'ask-all':
            # TODO - track msg ideas and use for filtering
            query = content.get('content')
            query_string = query.to_string()
            if query.head() in self.asks and query_string in self.subscribers:
                self.subscribers[query_string].append(msg)
                self.subcribe_data_old[query_string] = None
                self.subcribe_data_new[query_string] = None
                reply_msg = KQMLPerformative('tell')
                reply_msg.set(':sender', self.name)
                reply_msg.set('content', ':ok')
                self.reply(msg, reply_msg)

    def receive_other_performative(self, msg):
        """Override of KQMLModule default... ping isn't currently supported by
        pykqml so we handle other to catch ping and otherwise throw an error.

        Arguments:
            msg {KQMLPerformative} -- other type of performative, if ping we
                                      reply with a ping update otherwise error
        """
        if msg.head() == 'ping':
            reply_content = KQMLList([':agent', self.name])
            reply_content.append(':uptime')
            reply_content.append(self._uptime())
            # TODO - check if .set('status', ':OK') can be used here instead
            reply_content.append(':status')
            reply_content.append(':OK')
            reply_content.append(':state')
            reply_content.append('idle')
            reply_content.append(':machine')
            reply_content.append(socket.gethostname())
            reply = KQMLPerformative('update')
            reply.set('sender', self.name)
            # reply.set('receiver', msg.get('sender'))
            # reply.set('in-reply-to', msg.get('reply-with'))
            reply.set('content', reply_content)
            self.reply(msg, reply)
        else:
            self.error_reply(msg, 'unexpected performative: ' + str(msg))

    ###########################################################################
    #                                Threading                                #
    ###########################################################################

    def _poll_for_subscription_updates(self):
        """Goes through the subscription updates as they come in and properly
        respond to the query (with _response_to_query).
        """
        LOGGER.debug("Running subcription poller")
        while self.ready:
            for query, new_data in self.subcribe_data_new.items():
                if new_data is not None:
                    for msg in self.subscribers[query]:
                        ask = msg.get('content')
                        query = ask.get('content')
                        LOGGER.debug("Sending subscribe update for %s", query)
                        res_type = ask.get('response')
                        self._response_to_query(msg, query, new_data, res_type)
                        self.subcribe_data_old[query] = new_data
            for query, _ in self.subcribe_data_new.items():
                self.subcribe_data_new[query] = None
            time.sleep(self.polling_interval)

    def _listen(self):
        """Sets up input and output socket connections to our listener.

        Infinite loop while ready to connect to our listener socket. On connect
        we get the write socket as a Buffered Writer and the read socket as a
        KQML Reader (which passes through a Buffered Reader). The reader is
        then attached to a KQML Dispatcher which is subsequently started, and
        passed along to the executor (which is a thread pool manager).
        """
        LOGGER.debug('listening')
        # print(self.dispatcher.receiver)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            while self.ready:
                connection, _ = self.listen_socket.accept()
                LOGGER.debug('received connection')
                socket_write = socket.SocketIO(connection, 'w')
                self.out = io.BufferedWriter(socket_write)
                socket_read = socket.SocketIO(connection, 'r')
                read_input = KQMLReader(io.BufferedReader(socket_read))
                self.dispatcher = KQMLDispatcher(self, read_input, self.name)
                executor.submit(self.dispatcher.start)
                # print(self.out)
                # print(self.dispatcher.reader)

    ###########################################################################
    #                             General helpers                             #
    ###########################################################################

    def _response_to_query(self, msg, content, results, response_type):
        """Based on the response type, will create a properly formed reply
        with the results either input as patterns or bound to the arguments
        from the results. The reply is a tell which is then sent to Companions.

        Goes through the arguments and the results together to either bind a
        argument to the result or simple return the result in the place of that
        argument. The reply content is filled with these argument/result lists
        (they are listified before appending) before being added to the tell
        message and subsequently sent off to Companions.

        Arguments:
            msg {KQMLPerformative} -- the message being passed along to reply
            content {[type]} -- query, starts with a predicate and the
                                remainder is the arguments
            results {[type]} -- The results of performing the query
            response_type {[type]} -- the given response type, if it is not
                                      given or is given to be pattern, the
                                      variable will be set to True, otherwise
                                      False.
        """
        response_type = response_type is None or response_type == ':pattern'
        reply_content = KQMLList(content.head())
        results_list = results if isinstance(results, list) else [results]
        result_index = 0
        arg_len = len(content.data[1:])
        for i, each in enumerate(content.data[1:]):
            # if argument is a variable
            if str(each[0]) == '?':
                # if last argument and there's still more in results
                if i == arg_len and result_index < len(results_list)-1:
                    # get the remaining list
                    pattern = results_list[result_index:]
                    # pattern or binding...
                    reply_with = pattern if response_type else (each, pattern)
                    reply_content.append(listify(reply_with))
                else:
                    # same logic as above, just doesn't get the remaining list
                    pattern = results_list[result_index]
                    reply_with = pattern if response_type else (each, pattern)
                    reply_content.append(listify(reply_with))
                    result_index += 1
            else:
                if response_type:  # only add the arguments if this is pattern
                    reply_content.append(each)
        reply_msg = KQMLPerformative('tell')
        reply_msg.set('sender', self.name)
        reply_msg.set('content', reply_content)
        self.connect(self.host, self.port)
        self.reply(msg, reply_msg)

    def _close_socket(self):
        """shutsdown the dispatcher and closes the socket"""
        self.dispatcher.shutdown()
        self.socket.close()

    def _uptime(self):
        """Cyc-style time since start (includes leap years)

        Returns:
            str -- string of the form
                    '(years months days hours minutes seconds)'
                   where years, months, days, etc are the uptime in number of
                   years, months, days, etc.
        """
        now = datetime.now()
        years = now.year - self.starttime.year
        # months
        if now.year == self.starttime.year:
            months = now.month - self.starttime.month
        else:
            months = 12 - self.starttime.month + now.month
        # days
        if now.month == self.starttime.month:
            days = now.day - self.starttime.day
        elif self.starttime.month in [1, 3, 5, 7, 8, 10, 12]:
            days = 31 - self.starttime.day + now.day
        elif self.starttime.month in [4, 6, 9, 11]:
            days = 30 - self.starttime.day + now.day
        else:
            days = 28 - self.starttime.day + now.day
        year_list = range(self.starttime.year, now.year+1)
        extra_days = sum(map(int, [is_leap(year) for year in year_list]))
        days += extra_days
        # hours
        if self.starttime.day == now.day:
            hours = now.hour - self.starttime.hour
        else:
            hours = 24 - self.starttime.hour + now.hour
        # minutes
        if self.starttime.hour == now.hour:
            minutes = now.minute - self.starttime.minute
        else:
            minutes = 60 - self.starttime.minute + now.minute
        # seconds
        if self.starttime.minute == now.minute:
            seconds = now.second - self.starttime.second
        else:
            seconds = 60 - self.starttime.second + now.second
        time_list = [years, months, days, hours, minutes, seconds]
        # return '({})'.format(" ".join(map(str, time_list)))
        return f'({" ".join(map(str, time_list))})'

###############################################################################
#                          Class Helper Functions                             #
###############################################################################


def is_leap(year):
    """returns True if the given year was a leap year, otherwise False.

    Written to sooth the complaints from pycodestyle and pyflakes regarding
    this "one-line" lambda that works but is rather ugly and un-pythonic.
    is_leap = lambda y: True if y % 400 is 0 else False if y % 100 is 0 \
        else True if y % 4 is 0 else False

    Arguments:
        year {int} -- a year

    Returns:
        bool -- whether or not the given year was a leap year
    """
    if year % 400 == 0:
        if year % 100 == 0:
            if year % 4 == 0:
                return True
            return False
        return True
    return False


# pylint: disable=too-many-return-statements
# Eight is reasonable in this case, need to break down many data types.
def listify(possible_list):
    """Takes in an object and returns it in KQMLList form.

    Checks if the input is a list, and if so it recurses through all entities
    in the list to further listify them. If the input is not a list but is
    instead a tuple of length 2 we make the assumption that this is a dotted
    pair and construct the KQMLList as such, otherwise we treat this larger
    tuple the same as a list. If the input is a string, we first check that it
    has a space in it (to differentiate facts, strings, and tokens). We then
    check if it is in lisp form (i.e. '(...)') and if so we split every term
    between the parens by the spaces. Otherwise we return the object as a
    KQMLString. In either case, if the string had no spaces in it we return it
    as a KQMLToken. WARNING: This may be an incomplete breakdown of strings.
    Next we check if the input was a dictionary and if so we listify the key
    value pairs, and then make a KQMLList of that overall list of pairs.
    Lastly, if the input was nothing else we return the input as a string
    turned into a KQMLToken.

    Arguments:
        possible_list {any} -- any input that you want to transform to KQML
                               ready data types

    Returns:
        KQML* -- List, String, or Token
    """
    # pylint: disable=no-else-return
    # Another pylint bug...? Normally this error is for having return
    # statements inside an else but this is showing up for return statements in
    # elif. Not something to worry about.
    if isinstance(possible_list, list):
        new_list = [listify(each) for each in possible_list]
        return KQMLList(new_list)
    elif isinstance(possible_list, tuple):
        if len(possible_list) == 2:
            car = listify(possible_list[0])
            cdr = listify(possible_list[1])
            return KQMLList([car, KQMLToken('.'), cdr])
        new_list = [listify(each) for each in possible_list]
        return KQMLList(new_list)
    elif isinstance(possible_list, str):
        if ' ' in possible_list:
            # WARNING: This may be an incomplete breakdown of strings.
            if possible_list[0] == '(' and possible_list[-1] == ')':
                terms = possible_list[1:-1].split()
                return KQMLList([listify(t) for t in terms])
            return KQMLString(possible_list)
        return KQMLToken(possible_list)
    elif isinstance(possible_list, dict):
        return KQMLList([listify(pair) for pair in possible_list.items()])
    return KQMLToken(str(possible_list))

###############################################################################
#                        General Utility Functions                            #
###############################################################################


def convert_to_boolean(to_be_bool):
    """Since KQML is based on lisp, and (at least for now) messages are coming
    from lisp land (i.e., Companion), we use some lisp conventions to
    determine how a KQML element should be converted to a Boolean.

    If the KQML element is <code>nil</code> or <code>()</code> then
    <code>convert_to_boolean</code> will return <code>False</code>. Otherwise,
    it returns <code>True</code>.

    Arguments:
        to_be_bool {any} -- KQMLToken and KQMLList will be properly converted
                            to Lisp style nil, anything else is True.

    Returns:
        bool -- False if Lisp style nil, True otherwise
    """
    if isinstance(to_be_bool, KQMLToken) and to_be_bool.data == "nil":
        return False
    # pylint: disable=len-as-condition
    # This is an issue that pylint is fixing in release 2.4.0. len(seq) == 0
    # is okay (just len(seq) isn't).
    if isinstance(to_be_bool, KQMLList) and len(to_be_bool) == 0:
        return False
    return True


def convert_to_int(to_be_int):
    """Most data being received by Pythonian will be a KQMLToken. This function
    gets the data of the KQMLToken and casts it to an int.

    Arguments:
        to_be_int {any} -- converts the data in a KQMLToken or KQMLList to an
        int, other data types will be passed through without conversion.

    Returns:
        any -- int if the data in a token or String can be made into an int,
        otherwise we pass the input through
    """
    if isinstance(to_be_int, KQMLToken):
        return int(to_be_int.data)
    if isinstance(to_be_int, KQMLString):
        return int(to_be_int.data)
    # TODO - Throw error
    return to_be_int


# NOT USED
# TODO - name change? - convert to list might not be a good name
def convert_to_list(to_be_list):
    """Returns list data

    Arguments:
        to_be_list {any} -- KQMLList to get the data out, anything else is
        passed along

    Returns:
        any -- list data if input was KQMLList, otherwise input
    """
    if isinstance(to_be_list, KQMLList):
        return to_be_list.data  # could recurse but.... nah!
    return to_be_list


def test(test_input):
    """test function for simple Pythonian test agent to use for achieve

    Arguments:
        test_input {any} -- thing to be printed

    Returns:
        number -- 1, always 1. For testing purposes.
    """
    print(str(test_input))
    return 1

###############################################################################
#                               Run as Main                                   #
###############################################################################


if __name__ == "__main__":
    LOGGER.setLevel(logging.DEBUG)
    AGENT = Pythonian(host='localhost', port=9000, localPort=8950, debug=True)
    AGENT.add_achieve('test', test)
    AGENT.achieve_on_agent('interaction-manager', "(initializeToMExp ?gpool)")
