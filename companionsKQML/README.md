# companionsKQML Package

Package containing all basic Companions related KQML communication for Python. For detailed documentation of functions and objects see [docs](https://github.com/SamuelHill/companionsKQML/tree/master/docs).

## companionsKQMLModule.py

Module replacing [pykqml's KQMLModule](https://github.com/bgyori/pykqml/blob/master/kqml/kqml_module.py). Handles all low level actions relevant to keeping the module alive as a KQML server compatible with Companions (for more on the reasoning for this see archive/README.md). This includes;
* a threaded socket server listening for messages (on the listener_port),
* modified connect and send;
  * send now opens the send socket, sends the message, and closes the socket for every sent message so Companions knows that the message is over and doesn't time out,
* safe exit function that cleans up everything and closes (great for the REPL and for applications that don't need to stay alive forever),
* all the basic functions for registering as an agent and keeping up with status update pings,
* respond to query mechanism that will either pass back binding lists or will bind the results to the query pattern

As well, there are several convenience functions such as `parse_command_line_args` which can create an agent from command line flags, `listify` which takes any object in python and converts it into the correlated pykqml KQML object, `performative` which creates KQML messages from strings to be sent along, and `convert_to_boolean` & `convert_to_int` which take the KQML data you get back and convert them to normal python types.

## pythonian.py

Pythonian agent handles;
* receiving tells,
* receiving ask-ones and adding functions to be called by those ask-ones,
* sending achieves,
* receiving achieves and adding functions to be called by those achieves,
* add a subscription pattern (advertises that subscription),
* receive new subscribers for a pattern,
* update the data for a subscription,
* insert data into a kb,
* insert data to a microtheory,
* and insert a list of facts to a microtheory.

In other words, the simplified API is that this agent can handle asks, achieves, subscriptions, and tells in KQML from Companions and as well can send achieves and inserts to Companions itself.

Note: This should be easy to extend to other kqml performatives, add whatever receive_* query you want (based on what pykqml offers) and handle the incoming message appropriately.
