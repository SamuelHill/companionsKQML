# Test Agent

The Test Agent is being developed to test the functionality of a Pythonian agent when connected to Companions. You can also use this code as an example to see how Pythonian works.

## Running the agent:

To test this agent you will need to start a Companion, start the Test Agent, and then send messages to the Test Agent from Companion:

1. Start Companions, allowing the Companion to listen for new agents. The executable does this by default. If running from source code, try:
```cl
(cl-user::start-companion :scheme :mixed)
```
If you are seeing errors about the facilitator "actively refuses" the message, this is because the companion is running with the transport scheme set to :queue. Shut everything down and re-launch the companion using the above command.

2. Start the Test Agent, run (in an environment with companionsKQML installed):
```
python3 test_agent.py
```

3. Send a message:
    1. From the Session Manager, go to the Commands tab and enter the following message:
    ```cl
    (achieve :receiver TestAgent :content (task :action (test_achieve data)))
    ```
    To verify the agent received this, look in the console window where Pythonian is running and find a debug statement saying something like "testing achieve with \_input data".

    2. From the listener, enter the following:
    ```cl
    (agents::send *facilitator* 'TestAgent '(achieve :content (task :action (test_achieve_return nil))))
    ```
    To verify that Companions is receiving a reply from this, you should see a nil printed out in the listener soon after executing the above command.

To test the insert or subscription mechanisms, uncomment those sections from the bottom of your test file. To verify an insert worked browse the kb for the inserted fact. For more on testing subscriptions see the [subscribe section on the main README.md](https://github.com/SamuelHill/companionsKQML#subscribe).
