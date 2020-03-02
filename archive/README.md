# CompanionsKQML and Pythonian History

The new Pythonian agent architecture is a upgrade from the previous Pythonian agent ([Companions/Pythonian2](http://www.qrgwiki.qrg.northwestern.edu/index.php?title=Companions/Pythonian2)), which itself was a replacement of the original [Companions/Python-Agent](http://www.qrgwiki.qrg.northwestern.edu/index.php?title=Companions/Python-Agent).

## Reasoning for updates

The new architecture takes portions of the pykqml framework (KQML python objects, read and dispatching on kqml messages, etc.) and re-architects the main KQMLModule which controls things like connecting to an agent and sending messages. The two main reasons for this changes are;
1. To simplify how the KQML server was working (both in terms of sending and receiving) from the convoluted model built on *top* of KQMLModule,
2. To pull out the pythonian agent code which has became obfuscated by the lower level controlling mechanisms.

The previous model is only convoluted because of the requirements Companions has for a socket server and the nature of how the pykqml module works. Namely, Companions sends eof after every command while the KQMLModule shuts down after an eof, and Companions waits for a socket to close after receiving a message because some connections to Companions can take a long time and if not shut off the Companions will timeout. Regardless this re-architecture solves a few issues that resulted from the convoluted model and it's obfuscation of the pythonian code such as;
* Kqml socket server reseting the output connection as well on new incoming connections, effectively disabling send. This could have been solved by added connect (by the way the connect would reset the input connection too...) and disconnect everywhere we sent - and sure enough this technique was used - but a cleaner solution is to just redo send, connect, and the listener.
* Subscriptions being lumped in with asks despite never calling a stored ask function.

## Files

* *agents.py* - old python agent, pre pykqml
* *companions_connect.py* - helper code for finding and launching companions, also helper code for launching Pythonian agent from command line, incorporated later
* *kqml_parser.py* - old attempt at kqml parsing, pre pykqml
* *pythonian_v2-1_begin_revision.py* - first attempts at simplifying (subscriptions, dateutil, ask architecture)
* *pythonian_v2.py* - Pythonian2 as of last SVN push, (i.e. not the first iteration of the pythonian agent with pykqml)
* *pythonian_v3_test_no_threads.py* - pykqml architecture test to see what we rely on and how to rebuild it
* *socketTest.py* - old socket testing code, dead simple
* *socketTest2.py* - old socket testing code, dead simple
* *subscriptions.py* - subscription helper classes, incorporated later
* *test_agent_old.py* - old version of the test agent
