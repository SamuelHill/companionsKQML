# CompanionsKQML and Pythonian

This page describes the new Pythonian agent architecture. For a history and some of the reasoning behind the architecture choices see the [archive folder and associated README.md](https://github.com/SamuelHill/companionsKQML/tree/master/archive). For a simple (high level) catalog of the features available in this package see the [README.md in the companionsKQML folder](https://github.com/SamuelHill/companionsKQML/tree/master/companionsKQML). For a detailed documentation of the available functions and objects see the [docs folder and associated README.md](https://github.com/SamuelHill/companionsKQML/tree/master/docs). For an example agent or to test the system with Companions see the [test folder and associated README.md](https://github.com/SamuelHill/companionsKQML/tree/master/test).

## Install

`python3 -m pip install companionsKQML`

[See us on pypi](https://pypi.org/project/companionsKQML/)!

## System requirements

1. Companions
2. Python >= 3.6 (may work for some other 3.x versions, currently being tested in 3.6.5)
3. pip (to install this package and all dependencies)

## FAQ

See the [FAQ](https://github.com/SamuelHill/companionsKQML/blob/master/FAQ.md)!

## Making a Pythonian agent

If you want Companion to have access to some functionality in python, you can create a Pythonian agent to meet that need. Generally, it is suggested you make a new Pythonian agent and not arbitrarily add to an existing one. For example, if you want functionality from spacy, then it is suggested that you create a new spacy agent. An obvious exception to this is if an existing agent is strongly related to the new desired functionality and uses the same python modules.

To create a new Pythonian agent, you will create a python class that extends Pythonian. In this class, you will implement the desired functionality via adding asks, achieves, or subscription patterns in the `__init__` method. The asks and achieves require functions to either use for responding to an ask or achieve on, and normally these functions are also defined inside the class, but these functions can technically come from anywhere so long as they are callable. The only other times you must put code inside the class is when you want to generally use the kqml message sending capabilities. For an indepth example check of the [test/test_agent.py code](https://github.com/SamuelHill/companionsKQML/blob/master/test/test_agent.py). The basic setup is:

```python3
class CustomPythonianAgent(Pythonian):
    name = "CustomPythonianAgent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # your setup code here...
```

To instantiate the agent when calling this module, there is a convenience function you can use to allow for command line arguments to specify a handful of parameters at runtime. As well as allowing for more flexible agents, the convenience function has a further nicety in that it will attempt to check for a running Companions agent on your system and, if found, can get the port it is hosted at automatically. This extra feature is also available through the `init_check_companions` constructor as we want the `__init__` method to remain simple. The command line argument function is called as follows:

```python3
if __name__ == "__main__":
    AGENT = CustomPythonianAgent.parse_command_line_args()
```

This function parses the sys.args list and passes the appropriate flagged values along to create a new instance of the class. The flags associated with this function are:
* -u (--url) followed by some string, url where Companions kqml server is hosted - corresponds to host kwarg (-h is taken by help)
* -p (--port) followed by some int, port Companions kqml server is open on
* -l (--listener_port) followed by some int, port pythonian kqml server is open on
* -d (--debug) present stores true - this overrides the default value in init, whether or not to log debug messages
* -v (--verify_port) present stores true - this matches the default value in init_check_companions, whether or not to verify the port number by checking the pid in the portnum.dat file (created by either running Companions locally or in an exe) against the pid found on the running process where the portnum.dat file was found. This again is only applicable to starting an agent using this function, and this verify is just a more stringent test on the port number for our extra search for Companions.

To utilize the check for companions on its own without expecting command line args (any time you may want to benefit from detecting a running companion but are not running the agent you create as a module):

```python3
if __name__ == "__main__":
    AGENT = CustomPythonianAgent.init_check_companions()
```

This function will take the exact same keyword arguments as the the `__init__` function below with the addition of a *verify_port* boolean that defaults to false. The verify_port keyword has the same function as the flag by the same name used in the `parse_command_line_args` function.

Alternatively, you can just create the agent through the normal `__init__` and use keyword arguments to specify a handful of parameters:

```python3
if __name__ == "__main__":
    AGENT = CustomPythonianAgent()
```

The parameters (`kwargs`) are *host* (default = `'localhost'`), *port* (default = `9000`), *listener_port* (default = `8950`), and *debug* (default = `False`). If you are running a Companion on a different machine set *host* to be the ip address (as a string) with the *port* properly set. The *listener_port* is the port that you will be sending messages from so set it according to any firewall or other port blocking that you may have, this shouldn't be a problem for local work (Companions on the same machine). *Debug* sets the logger level so a value of `True` will print all debug and log statements to the console (console logging is the default behavior we use) while a value of `False` will only print the log statements.

## Receiving performatives from Companions

Companions may communicate with a Pythonian agent by sending KQML messages to it. The head of each message indicates the performative of the message. The sections below describe the performatives that are currently supported and how to add that functionality to your pythonian agent.

### achieve

If you want a function to be available to Companion via an achieve message, then you will need to add the function to the achieves that the agent knows about. This can be done in the `__init__` method like so:

```python3
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.add_achieve(my_custom_achieve_function)
```

where `my_custom_achieve_function` is some function you have defined. Alternatively you can define the function inside the class and pass it along as `self.my_custom_achieve_function` - this is shown in the test code with static functions. Additionaly, if you would like to give the ask a name to be called by Companions other than the function name you can write:

```python3
self.add_achieve(my_custom_achieve_function, 'new_function_name')
```

The number of arguments to pass along when calling this achieve from companions is determined by the number of args in the function you define. As of now functions that have a self argument won't work, and functions that have a default value defined won't have that value respected and that argument contributes to the number of expected arguments. For all other functions, so long as you pass the same number of args the function will be called with those args. To summarize an example in [test/test_agent.py](https://github.com/SamuelHill/companionsKQML/blob/master/test/test_agent.py), we define test_acheive to have one argument:

```python3
def test_achieve(input: Any):
    pass
```

And we call this function with an achieve like `(achieve :receiver YourAgent :content (task :action (test_achieve data)))`. Focus on the `(test_achieve data)`, this is the 'call' to your achieve function. If you added this function with a new name that call would be `(new_function_name data)` instead. If your function had 4 arguments for the inputs then you would call something like `(new_function_name data1 data2 data3 data4)`.

The return value of this function will be sent to Companions via a tell message. The return is sent as a tell to Companions with the content set to the return value passed through the *listify* function (converts python objects to KQML equivalents). This means that you should be able to return most objects from your functions (at a minimum the objects passed in need to be able to be turned to strings).

### ask-one

If you want to make a query available to Companion via an ask message, then you will need to add a function to the class to perform the processing necessary for the query. To recognize that function as a query, you need to add it to the asks the agent knows about in much the same way that you add and achieve. The major difference in how asks and achieve work then is based on the call and return structure. Achieves achieve a task with some function while asks reply to querys with the requested informationm, this is accomplished by calling the python function and binding the returned results to the query pattern. As such, in addition to the name of the ask (the predicate) and the function to be called, you may want to note how the query pattern should be formed for easy reference. For example, the code below (inside `__init__`) adds a function we have defined to the agents ask predicates which only takes in one input and should only return one element.

```python3
# (my_custom_ask_function input_data ?return)
self.add_ask(my_custom_ask_function)
```

Similar to how you can add a custom name for achieves, you can add custom names for asks:

```python3
# (new_function_name input_data ?return)
self.add_ask(my_custom_ask_function, 'new_function_name')
```

The return value of this function will be sent to Companion via a tell message. The return value should have the same number (or greater) of elements as there are variables in the query. This means the return value should either be a single element (`None` included) or a list of elements, and all elements should be able to be turned into strings (they have a `__str__` method in the object). The return is sent back to Companions via the response to query mechanism in CompanionsKQMLModule, in this function the response sent back is either a binding list of variables to elements in the results, or a pattern substitution (default) with the variables in the ask substituted by the result elements.

### subscribe

Subscriptions are a little more complicated as is it requires both advertising a subscription and subscribing to it before you can start updating the subscribers for a given subscription. However, to make this easier the `add_subscription` function handles advertising the subscription for you (which can even be put inside the init after the super init call to advertise immediately after registering). For example, to advertise the `'(custom_query_pattern ?x)'` pattern:

```python3
self.add_subscription('(custom_query_pattern ?x)')  # inside __init__ function...
```

Once the subscription is advertised Companions agents can subscribe to it via subscribe messages that tell the pythonian agent to respond (with a tell) when any updates to a given query are found. The query that an agent is subscribing to needs to be one that the pythonian agent is advertising as subscribable. An example of the session-reasoner subscribing to junk mail is the following (not sure on the proper way to do this from Companions ui, this is from lisp console):

```cl
(agents::subscribe-to-all *sr* '(custom_query_pattern ?x) #'print-reply-callback)
```

Once you have subscribers to a subscription, you can start updating the data relevant to your query via the `update_subscription` function. This function needs to have the same pattern that you passed in to `add_subscription`. For example, to update the above pattern we can make a function in our class that always will link to that subscription pattern:

```python3
def update_custom_query_pattern(self, data):
    self.update_subscription('(custom_query_pattern ?x)', data)
```

A note, the pattern is sent back to Companions in a tell as either the input data bound to the variables in the pattern or as a binding list. Make sure that the data can properly map onto the variables in the pattern.

### tell

When the Companion sends a tell to the pythonian agent, it currently logs the message and sends a None in response. This is useful for debugging and can be overwritten if a specific tell functionality is needed.

### ping

You do not need to do anything for this, as the Pythonian agent will automatically reply to this message. However, if you do not want the log cluttered with ping updates, inside Companions click the 'Toggle status updates' button to stop sending those pings.

## Sending performatives to Companions

### insert

To push new knowledge to Companions, a Pythonian agent may use the insert performative. This will take some data (which is the content of the performative) and send it to Companions. On the Companions side, this will be added to working memory and be added to the KB. If you want to have it only go to WM and not the KB, then there is a WM-only flag. There are functions available for inserting single facts, inserting into a microtheory, and inserting a list of facts as a microtheory.

Note that many use cases should probably use subscriptions instead of just pushing data to Companions. Subscriptions allow an agent to indicate that it is looking for certain pieces of knowledge, and when another agent acquires that knowledge it sends it off to the subscribing agent. This is ideal for asynchronous interactions between the agents, and a good use case is when a human is interacting with the Companion and you want Companion to go off an do something while the interaction continues.

### achieve_on_agent

A Pythonian agent can use `achieve_on_agent` to send a message to a Companions agent to kick off a command via achieve. It takes some data (a string in the form of a plan call) and the name of the agent that should perform the achieve. Of course, the achieve needs to be defined on the Companion's side.

## Managing data types

KQML has a syntax similar to lisp and to make utilizing KQML easier pykqml has several objects that are both generated from parsing messages and used in the sending of messages. On top of these objects we have added two methods which simplify transforming python type objects into KQML objects. In addition to the methods that convert from python to the expected KQML objects, there are two functions for converting from the KQML objects to python type objects. All four of these helper functions live in companionsKQMLModule to help keep Pythonian clear of lower level details.

### listify

Listify takes in any python object and returns the appropriate KQML object from pykqml. Listify readily handles lists, dicts, bools, strings, and tuples, and can handle any other object that has a str representation. Some examples of its use:

```python3
>>> listify(['a', 3, 0.7, 'this'])
(a 3 0.7 this)
>>> f'(data {_})'
'(data (a 3 0.7 this))'
>>>
>>> listify('a stiring')
"a string"
>>> listify('atom')
atom
>>> listify(('atom', 'cell'))
(atom . cell)
>>> listify({'atom': 'cell', 'test': 'dict'})
((atom . cell) (test . dict))
>>> listify(False)
nil
>>> listify([1, [2, [3, 4]]])
(1 (2 (3 4)))
```

By passing your data into listify, you will get a KQMLObject in return which can easily be utilized in the formation of performatives. This is already an under the hood feature of achieves, asks, and subscriptions in that your returned objects will be listified for you (for ask and achieve functions) and your subscription data will be handled upon updating (you pass data to be bound to arguments which is then listified). A note, insert data does not listify your data as it expects you to be passing in a fact that fits into a kqml query (a string that has proper parens and is the representation of a fact). However, in any other situation where you are creating a message (see performative) and want to process some data into a more appropriate form then you should use *listify*.

### performative

*performative* allows you to pass in a string with the well formed KQML query instead of creating a performative and setting each value (`msg = KQMLPerformative('achieve')` followed by `msg.set('content', data)`). So long as you remember to add colons before the key (e.g. `:content data`) and *close all parens*, creating well formed KQML strings isn't too hard. As well, we often are using a base query and filling in the blanks so fstrings fit this task quite well. You can still set new key value pairs on the KQMLPerformative object returned by a call to *performative* to do any modifications to your template. Some examples of it's use:

```python3
# Inside some function that you want to send a message from
# (inside a Pythonian agent):
message = (f'(ask-all :sender {self.name} :receiver session-reasoner '
           f':query-type ask :reply-with {reply_id} :context {context} '
           f':content {content})')
self.send(performative(message))

# Alternatively - constructed using KQMLObject methods:
message = KQMLPerformative('ask-all')
message.set('sender', self.name)
message.set('receiver', 'session-reasoner')
message.set('query-type', 'ask')
message.set('reply-with', reply_id)
message.set('context', context)
message.set('content', content)
self.send(message)

# You can also create the message first as a template f-string and then add
# to it as a KQMLObject
message = performative(f'(ask-all :sender {self.name} :receiver session-reasoner '
                       f':query-type ask :reply-with {reply_id} :context {context})')
message.set('content', content)
self.send(message)
```

This should allow you to quickly create a performative to be sent to companions, all that is needed is for you to figure out what query you want to send in the first place.

### convert_to_boolean

We use some lisp conventions to determine how a KQML element should be converted to a Boolean. If the KQML element is `nil` or `()` then `convert_to_boolean` will return `False`. Otherwise, it returns `True`.

### convert_to_int

If the KQML element is a `KQMLToken` or `KQMLString`, then the internal data of these tokens are cast to an int. Otherwise, the original value is returned cast to an int.

