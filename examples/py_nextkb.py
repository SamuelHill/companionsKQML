#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 3.6
# @Filename:    py_nextkb.py
# @Author:   Samuel Hill
# @Date:     2019-10-30 15:17:48
# @Last Modified by:    Samuel Hill
# @Last Modified time:  2021-07-11 13:04:14

"""
Pythonian module to hook up to NextKB.

Using a micro exe for companions - one with only the facilitor running, no
session manager, spatial reasoner, etc. - we connect via Pythonian as any
other python project would connect to the fully functioning companions. The
API that is detailed below is ment to faciliate the KQML-esk messages that are
passed between Pythonian and Companions such that any new python program can
simply ask for and access the knowledge within NextKB without learning how to
use Lisp, KQML, or companions.

Attributes:
    DEFAULT_ENVIRONMENT (bool): whether or not to make a query local or context
    DEFAULT_MICROTHEORY (str): default microtheory to use if none specified
    DEFAULT_NUM_ANSWERS (int): default number of answers if none specified
    DEFAULT_TRANSITIVE (bool): whether or not to make a query transitive
    LOGGER (TYPE): The logger (from logging) to handle debugging
    NOT_USING_MICROTHEORY (str): Flag for not using microtheory context,
        shouldn't be microtheories named like this
"""

from logging import getLogger, DEBUG, INFO
from time import sleep
from kqml import KQMLPerformative, KQMLList
from companionsKQML import performative, Pythonian

NOT_USING_MICROTHEORY = '!NOT USING MICROTHEORY!'
DEFAULT_MICROTHEORY = 'EverythingPSC'
DEFAULT_TRANSITIVE = True
DEFAULT_ENVIRONMENT = True
DEFAULT_NUM_ANSWERS = 10
LOGGER = getLogger(__name__)


###############################################################################
#                               NextKB Agent                                  #
###############################################################################

class NextKBAgent(Pythonian):
    """Pythonian Module to hook up to NextKB, adds an answer cache for linking
    responses to queries back to the function that called them

    Attributes:
        answer_cache (dict): stores the responses to queries based on the
            reply_id
        kb_response_interval (int): how often to check for a KB response when
            waiting
        name (str): This is the name of the agent to register with
        response_id (int): id to keep track of queries and associated answers
    """
    name = "NextKBAgent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.debug:
            LOGGER.setLevel(DEBUG)
        else:
            LOGGER.setLevel(INFO)
        self.response_id = 0
        self.answer_cache = {}
        self.kb_response_interval = 1

    def receive_tell(self, msg: KQMLPerformative, content: KQMLList):
        reply_to = str(msg.get('in-reply-to'))
        if reply_to:
            self.answer_cache[reply_to] = content
        super().receive_tell(msg, content)

    def _new_response_id(self) -> str:
        self.response_id += 1
        return f'py_nextkb_query_id{self.response_id}'

    def _wait_on_response(self, content: str,
                          microtheory: str = None) -> KQMLList:
        """Builds off of _kqml_ask_all to add a reply_id and properly handle
        the responses coming in from Companions tells. WAITS FOR RESPONSES,
        this is blocking and will be in a wait loop until a response comes in.

        Args:
            content (str): the actual query you want to make
            microtheory (str, optional): the microtheory to use as context, to
                ignore the microtheory and not have a context pass
                NOT_USING_MICROTHEORY instead of a string. Defaults to using
                DEFAULT_MICROTHEORY if nothing is passed in (or None is passed)

        Returns:
            KQMLList: content of the response query
        """
        reply_with = self._new_response_id()
        self.answer_cache[reply_with] = None
        self.send(self._kqml_ask_all(reply_with, content, microtheory))
        LOGGER.debug('Waiting for response to %s...', reply_with)
        while self.answer_cache[reply_with] is None:  # wait for response
            sleep(self.kb_response_interval)
        response = self.answer_cache[reply_with]
        LOGGER.debug('Response to %s: %s', reply_with, response)
        return response

    def _kqml_ask_all(self, reply_id: str, content: str,
                      microtheory: str = None) -> KQMLPerformative:
        """Message creation for ask-all's to session-reasoner.

        Args:
            reply_id (str): id to reply with
            content (str): the actual query you want to make
            microtheory (str, optional): the microtheory to use as context, if
                the string is equal to the default NOT_USING_MICROTHEORY then
                we do not use a context. Defaults to using DEFAULT_MICROTHEORY
                if nothing is passed in (or None is passed)

        Returns:
            KQMLPerformative: the KQML ask-all message to be sent, messages are
                of the form -
                '(ask-all :sender NextKBAgent
                          :receiver session-reasoner
                          :query-type ask
                          :reply-with reply_id
                          [:context microtheory] <- optional
                          :content content)'
        """
        context = microtheory == NOT_USING_MICROTHEORY
        mt_none = microtheory is None
        microtheory = DEFAULT_MICROTHEORY if mt_none else microtheory
        context = f':context {microtheory}' if context else ''
        message = (f'(ask-all :sender {self.name} :receiver session-reasoner '
                   f':query-type ask :reply-with {reply_id} {context} :content'
                   f' {content})')
        LOGGER.debug('KQML message %s', message)
        return performative(message)

    ###########################################################################
    #                                   API                                   #
    ###########################################################################

    # (ask-all :receiver session-reasoner :query-type ask :context BiologyMt
    #  :content (useTransitiveInference (contextEnvAllowed (isa Dog ?x))))
    def get_isas(self, token: str, microtheory: str = None,
                 transitive: bool = None, env: bool = None) -> KQMLList:
        """Queries for all the things that token is (has an isa relation with)
        in the KB. Basic query is of the form (isa <token> ?x).

        Args:
            token (str): item in the KB to query for
            microtheory (str, optional): microtheory to limit context by
            transitive (bool, optional): whether or not to make this transitive
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = f'(isa {token} ?x)'
        content = _transitive_wrapper(content, transitive)
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)

    def get_genls(self, token: str, microtheory: str = None,
                  transitive: bool = None, env: bool = None) -> KQMLList:
        """Queries for all the things that token is a generic version of (has
        a genls relation with) in the KB. Basic query is of the form
        (genls <token> ?x).

        Args:
            token (str): item in the KB to query for
            microtheory (str, optional): microtheory to limit context by
            transitive (bool, optional): whether or not to make this transitive
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = f'(genls {token} ?x)'
        content = _transitive_wrapper(content, transitive)
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)

    def get_facts_from_mt(self, microtheory: str) -> KQMLList:
        """Queries for all facts in a microtheory. Basic query is of the form
        (ist-Information <microtheory> ?x)

        Args:
            microtheory (str): microtheory to search for facts in, does NOT
                rely on default microtheory is None is passed in

        Returns:
            KQMLList: content of the response query
        """
        content = f'(ist-Information {microtheory} ?x)'
        return self._wait_on_response(content, NOT_USING_MICROTHEORY)

    def get_mts_for_fact(self, fact: str) -> KQMLList:
        """Queries for all microtheories that contain the given fact. Basic
        query is of the form (ist-Information ?x <fact>)

        Args:
            fact (str): fact to search for matching microtheories to

        Returns:
            KQMLList: content of the response query
        """
        content = f'(ist-Information ?x {fact})'
        return self._wait_on_response(content, NOT_USING_MICROTHEORY)

    def get_instances_col(self, col: str, microtheory: str = None,
                          env: bool = None) -> KQMLList:
        """Gets all instances of a collection. Basic query is of the form
        (isa ?x <col>)

        Args:
            col (str): collection to search for
            microtheory (str, optional): microtheory to limit context by
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = f'(isa ?x {col})'
        content = _transitive_wrapper(content, True)
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)

    def get_instances_pred(self, pred: str, microtheory: str = None,
                           env: bool = None) -> KQMLList:
        """Get all instances of the predicate. Basic query is of the form
        (and (assertedTermSentences <pred> ?fact)
             (operatorFormulas <pred> ?fact))

        Args:
            pred (str): predicate to search for
            microtheory (str, optional): microtheory to limit context by
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = (f'(and (assertedTermSentences {pred} ?fact)'
                   f'(operatorFormulas {pred} ?fact))')
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)

    def get_arity(self, relation: str) -> KQMLList:
        """Get the arity of the given relation. Basic query is of the form
        (arity <relation> ?num)

        Args:
            relation (str): the relation to query for

        Returns:
            KQMLList: content of the response query
        """
        content = f'(arity {relation} ?num)'
        return self._wait_on_response(content, NOT_USING_MICROTHEORY)

    # pylint: disable=too-many-arguments
    def retrieve_it(self, pattern: str, microtheory: str = None,
                    transitive: bool = None, env: bool = None,
                    num_answers: int = None) -> KQMLList:
        """Gets the pattern from the kb.

        Args:
            pattern (str): pattern to retrieve from the KB
            microtheory (str, optional): microtheory to limit context by
            transitive (bool, optional): whether or not to make this transitive
            env (bool, optional): whether or not to make this local
            num_answers (int, optional): number of answers to return

        Returns:
            KQMLList: content of the response query
        """
        content = _transitive_wrapper(pattern, transitive)
        content = _environment_wrapper(content, env)
        content = _num_answers_wrapper(content, num_answers)
        content = f'(kbOnly {content})'
        return self._wait_on_response(content, microtheory)

    def retrieve_references(self, token: str, microtheory: str = None,
                            env: bool = None) -> KQMLList:
        """Get all references to a token. Basic query is of the form
        (assertedTermSentences <token> ?fact)

        Args:
            token (str): token to search for references to
            microtheory (str, optional): microtheory to limit context by
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = f'(assertedTermSentences {token} ?fact)'
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)

    def get_axioms_from_mt(self, microtheory: str,
                           env: bool = None) -> KQMLList:
        """Get all axioms from a microtheory. Basic query is of the form
        (and (assertedTermSentences <== ?fact)
             (operatorFormulas <== ?fact))

        Args:
            microtheory (str): microtheory to limit context by
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = ('(and (assertedTermSentences <== ?fact)'
                   '(operatorFormulas <== ?fact))')
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)

    def get_axioms_for_relation(self, relation: str, microtheory: str = None,
                                env: bool = None) -> KQMLList:
        """Get the axioms that are relevant to the given relation. Basic query
        is of the form
        (and (assertedTermSentences <== ?fact)
             (operatorFormulas <== ?fact)
             (formulaArgument ?fact 1 ?conseq)
             (operatorFormulas <relation> ?conseq))


        Args:
            relation (str): relation to search for axioms with
            microtheory (str, optional): microtheory to limit context by
            env (bool, optional): whether or not to make this local

        Returns:
            KQMLList: content of the response query
        """
        content = ('(and (assertedTermSentences <== ?fact)'
                   ' (operatorFormulas <== ?fact)'
                   ' (formulaArgument ?fact 1 ?conseq)'
                   f' (operatorFormulas {relation} ?conseq))')
        content = _environment_wrapper(content, env)
        return self._wait_on_response(content, microtheory)


###############################################################################
#                              Content wrappers                               #
###############################################################################

def _environment_wrapper(content: str, env: bool = None) -> str:
    """Wraps the query (content) with the appropriate environment (local or
    contextEnv only).

    Args:
        content (str): query to be passed along
        env (bool, optional): whether to be contextEnv or local

    Returns:
        str: the environment wrapped query
    """
    env = DEFAULT_ENVIRONMENT if env is None else env
    if env:
        return f'(contextEnvAllowed {content})'
    return f'(localOnly {content})'


def _transitive_wrapper(content: str, trans: bool = None) -> str:
    """Wraps the query (content) with the appropriate transitive inference flag

    Args:
        content (str): query to be passed along
        trans (bool, optional): whether to use transitive inference or not

    Returns:
        str: the transitive use wrapped query
    """
    trans = DEFAULT_TRANSITIVE if trans is None else trans
    if trans:
        return f'(useTransitiveInference {content})'
    return f'(nonTransitiveInference {content})'


def _num_answers_wrapper(content: str, num_answers: int = None) -> str:
    """Wraps the query (content) with the appropriate numAnswers filter

    Args:
        content (str): query to be passed along
        num_answers (int, optional): number of answers to pass back

    Returns:
        str: the num answers wrapped query
    """
    num_answers = DEFAULT_NUM_ANSWERS if num_answers is None else num_answers
    return f'(numAnswers {num_answers} {content})'


###############################################################################
#                              Running NextKB                                 #
###############################################################################

if __name__ == '__main__':
    NEXT_KB = NextKBAgent.parse_command_line_args()
    print(NEXT_KB.get_isas('Dog'))
    NEXT_KB.exit()
