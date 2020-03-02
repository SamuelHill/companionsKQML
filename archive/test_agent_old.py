from pythonian import *
import logging
import time

logger = logging.getLogger('TestAgent')

class TestAgent(Pythonian):
    name = "TestAgent" # This is the name of the agent to register with

    def __init__(self, **kwargs):
        super(TestAgent, self).__init__(**kwargs)
        self.add_ask('test_ask_return_list1', self.test_ask_return_list1, '(test_ask_return_list1 ?_input ?return)')
        self.add_ask('test_ask_return_list2', self.test_ask_return_list2, '(test_ask_return_list2 ?_input ?return1 ?return2)')
        self.add_ask('test_ask_return_string', self.test_ask_return_string, '(test_ask_return_string ?_input ?return)')
        self.add_ask('test_ask_return_int', self.test_ask_return_int, '(test_ask_return_int ?_input ?return)')
        self.add_ask('test_ask_return_dict', self.test_ask_return_dict, '(test_ask_return_dict ?_input ?return)')
        self.add_ask('test_junk_mail', self.test_junk_mail, '(test_junk_mail ?x)', True)

        self.add_achieve('test_achieve', self.test_achieve)
        self.add_achieve('test_achieve_return', self.test_achieve_return)
        self.add_achieve('test_convert_boolean', self.test_convert_boolean)
        

    def test_ask_return_list1(self, _input):
        logger.debug('testing ask with _input ' + str(_input))
        return [_input]

    def test_ask_return_list2(self, _input):
        logger.debug('testing ask with _input ' + str(_input))
        return ["pass", "test"]

    def test_ask_return_string(self, _input):
        logger.debug('testing ask with _input ' + str(_input))
        return "pass"

    def test_ask_return_int(self, _input):
        logger.debug('testing ask with _input ' + str(_input))
        return 1

    def test_ask_return_dict(self, _input):
        logger.debug('testing ask with _input ' + str(_input))
        return {'key1':['a','b'], 'key2':'c'}

    def test_achieve(self, _input):
        logger.debug('testing achieve with _input ' + str(_input))


    def test_achieve_return(self, _input):
        logger.debug('testing achieve with _input ' + str(_input))
        return 1

    def test_convert_boolean(self, to_be_bool):
        logger.debug('testing boolean conversion with _input ' + str(to_be_bool))
        now_bool = convert_to_boolean(to_be_bool)
        logger.debug('new value: ' + str(now_bool))
        return now_bool

    def test_insert_to_Companion(self, data):
        logger.debug('testing inserting data into Companion with data: ' + str(data))
        Pythonian.insert_data(self, 'session-reasoner', data)

    def test_junk_mail(self, data):
        logger.debug('testing inserting data into Companion with data: ' + str(data))
        return "Send a million dollars to this address"

    def more_junk_mail(self, data):
        logger.debug('more junk mail has arrived')
        self.update_query('(test_junk_mail ?x)', data)

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    a = TestAgent(host='localhost', port=9000, localPort=8950, debug=True)
    #a.test_insert_to_Companion('(started TestAgent)')
    time.sleep(20)
    a.more_junk_mail('Click here for...')
    time.sleep(10)
    a.more_junk_mail('You have won!  Just send your SSN to us and we will send you the money')
