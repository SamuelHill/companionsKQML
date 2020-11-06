# FAQ

### Creating KQML messages?

See the performative and listify sections of the main [README.md](https://github.com/SamuelHill/companionsKQML/blob/master/README.md#listify).

### Listener port vs port?

Essentially we need one socket to send messages to companions over (to the facilitator) and another to receive message from companions on. There might be ways to get around this using the addressing inside the messages but this is doubly more work as adding this ability to use the same socket would also require companions to be reworked and this is very much a non issue. So, as stands companions uses different ports for each (non-lisp) agent. There is some other crossover of the port functionality as we send some messages over out listen port (such as ping), but generally:

- port = companions, facilitator (usually 9000, companions will tell you in the UI or the command prompt)
- listener port = your pythonian agent (defaults to the range 8950-9000)

These values can be hard coded in the init args, passed in at run time with the parse command line flags (-p and -l respectively), or - in most regular cases - specify nothing and have it magically connect.

### Multiple agents? / Previous agents?

As of 1.1.1 you should be able to have up to 50 pythonian agents running before you need to specify the listener port. If for some reason this isn't enough or you simply want to use a different port you should be able to use one of the above mentioned methodologies for changing the listener port. However, if you are using the previous pythonian (version 0, worked on up until 2018) the only way to change the port used for listening is to hardcode it in.

### Why are there timeouts in the debug log? / Why is the dispatcher disconnecting and reconnecting so much?

Prior to version 1.1 there may be some excess debug statements in the log. As of 1.1.1, unless you are in debug mode you should not see timeout or connect issues unless something is truly broken. In debug mode the dispatcher within pykqml disconnects and restarts on every message, including pings. Pings are normally on to give you uptime and status information but if they are cluttering your debug log you can turn off those updates in the companions ui by pressing the toggle status updates button on the right side.
