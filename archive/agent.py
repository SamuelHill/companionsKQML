### ALL FUNCTIONS CALLED BY ASK ARE GOING TO LIVE IN THE FILE functions.
### THIS HAS A HELPER TO INSTALL MISSING PACKAGES; USE WITH CAUTION
### TIME-INTENSIVE FUNCTIONS SHOULD BE SPUN OFF IN THREADS -
### IT'S YOUR JOB TO MAKE SURE THAT ITS ANSWERS ARE PASSED AROUND PROPERLY
### FOR TIME-INTENSIVE FUNCTIONS SET self.state = 'processing' FOR PINGS

import sys
import argparse
import socket
import threading
import numpy # because everything uses numpy
from datetime import datetime ## for uptime
from nltk.tokenize import regexp_tokenize

## local modules we've defined
import kqml_parser as kqml
import functions

# simple tester facilitator: (agents:start-facilitator (agents::who-am-i) 9000 (agents::available-nodes) :mixed)
# sample start up call: pythag = pythonian('127.0.0.1', 9000, 8090) 
# to ping, use lisp call: (agents::send *facilitator* 'pythonian '(ping))
# companion call: (achieve :receiver interaction-manager :content (labelImage "dog_frisbee" ?label))
# companion call for reading and storing: (achieve :receiver interaction-manager :content (labelReadAndStoreImage "dog_frisbee"))
# test image: call from lisp (agents::send *facilitator* 'pythonian '(ask-all :receiver pythonian :sender facilitator :content (labelImage "C:/qrg/companions/v1/pythonian/labelimg/images/dog_frisbee.jpg" ?label)))

class pythonian(object):
    performatives = ["ask-if", "ask-all", "ask-one", "stream-all", "eos", "tell", "untell", "deny", 
                     "insert", "uninsert", "delete-one", "delete-all", "undelete", "achieve", 
                     "unachieve", "advertise", "unadvertise", "subscribe", "error", "sorry", 
                     "standby", "ready", "next", "rest", "discard", "register", "unregister", 
                     "forward", "broadcast", "transport-address", "broker-one", "broker-all", 
                     "recommend-one", "recommend-all", "recruit-one", "recruit-all", 
                     "ping", "update", "room", "log", "checkpoint", "rollback", "shutdown", "login", "logout",
                     "spacy"]
    quick_queries = [] ## put queries that should NOT start on their own thread here
    fns = {}
    
    def __init__(self, facAdress, facPort, pyPort=8090, name = "pythonian", possibleQueries=["(labelImage ?image ?label)"]):    
        self.facAdress = facAdress
        self.facPort = facPort
        self.pyPort = pyPort
        self.sentMsgs = {}
        self.receivedMsgs = {}
        self.agents = {}
        self.messageCounter = 0
        self.possibleQueries = possibleQueries
        self.name = name
        self.starttime = datetime.now()
        self.state = 'idle'
        
        self.listenSoc = socket.socket()
        self.listenSoc.bind(("", pyPort))
	    #self.listenSoc.listen(10)
        print("connecting to facilitator on " + str(socket.gethostname()) + ":" + str(self.facPort))
        self.talkSoc = socket.socket()
        self.talkSoc.connect((self.facAdress, self.facPort))
        registermsg = '(register :sender ' + self.name + ' :receiver facilitator :content ("socket://localhost:' + str(self.pyPort) + '" nil nil ' + str(self.pyPort) + '))'
        #self.talkSoc.send(bytes(registermsg, 'utf-8'))
        self.talkSoc.send(registermsg)
        self.talkSoc.close()
        
        print("advertising")
        self.advertise()

        ### this next block of code resets the connection - not sure why it's needed
        #self.soc.close()
        #self.listenSoc = socket.socket()
        #self.listenSoc.bind(("", pyPort))
        #self.soc.settimeout(6000)
	
        print("listening")
        self.listenSoc.listen(10)
        self.listener = threading.Thread(target=self.listen, args = [])
        self.listener.start()
        
        self.spacy_obj = None
        
    def listen(self):
        while True:
            conn,addr = self.listenSoc.accept()
            msg = conn.recv(1024)
            if not msg: break
            self.readAndObey(msg, conn)

    def advertise(self):
        self.talkSoc = socket.socket()
        #self.soc.bind(("", self.pyPort))
        self.talkSoc.connect((socket.gethostname(), self.facPort))
        for queriable in self.possibleQueries:
            msg = "(advertise :sender pythonian " + \
                ":receiver facilitator " + \
                ":reply-with id" + str(self.messageCounter) + \
                " :content (ask-all " + \
                " :receiver pythonian " + \
                " :in-reply-to id" + str(self.messageCounter) + \
                " :content " + str(queriable) + "))"
            #self.talkSoc.send(bytes(msg, 'utf-8'))
            self.talkSoc.send(msg)
            self.messageCounter += 1
        self.talkSoc.close()

    def readAndObey(self,kqmlMsg,conn):
        print("reading")
        message = kqml.KQMLmessage(msg=str(kqmlMsg))

        print('message: ' + str(message))
        if 'content' in message.keys(): print("received message content: " + str(message['content'])) 
        method = getattr(self, message.performative.replace('-','_'))
        method(conn, message)

    def ping(self, conn, message):
        print("message = ", message)
        msg  = '(update :sender ' + self.name + ' :receiver ' + message['sender'] + \
            ' :in-reply-to ' + message['reply-with'] + ' :content (:agent ' + self.name + \
            ' :uptime ' + functions.uptime(self) + \
            ' :status :OK :state ' + self.state +  '))'
            ### lots of extra stuff could go in content: class, status, machine, etc.
        #conn.send(bytes(msg, 'utf-8'))
        conn.send(msg)
        conn.close()
       
    def achieve(self, conn, message):
        ## implicitly the same as ask_all
        self.ask_all(conn, message)

    #def task(self, conn, message):
        ## task is what content gets wrapped up in coming from 

    def ask_fn_content(self, conn, message):
        # it's assuming your function is defined in the functions file        
        if isinstance(message['content'], kqml.KQMLmessage) and message['content'].performative == 'task' and 'action' in message['content'].keys(): 
            ## currently specialized for the performative "task", which is what content gets wrapped in from external companion calls
            ## If we are ever passing nested KQML as content this will need to be split off somewhere else!
            #print("performative is task, message: " + str(message['content']))
            content = regexp_tokenize(str(message['content']['action'])[1:-1], pattern='"[^"]+"|[:()]|[\"a-zA-Z0-9\-\_\?\\\/\:\.\"]+')
            ## if any other KQML content, currently barfs!
        else:
            content = regexp_tokenize(str(message['content'])[1:-1], pattern='"[^"]+"|[:()]|[\"a-zA-Z0-9\-\_\?\\\/\:\.\"]+')
            print("performative: " + str(message['performative']))
            print("content: " + str(content))
        #fn = getattr(functions, content[0])
        fn = self.fns[content[0]]
        ## if it's a quick query, do it right away over the open socket. Otherwise, do it in a separate thread.
        return [fn, content]

    def ask_all(self, conn, message):
        [fn, content] = self.ask_fn_content(conn, message)
        if fn in pythonian.quick_queries: 
            self.openSocket_ask_all(message, conn, content, fn) ## not in its own thread
        else: 
            conn.close() ## close the old connection; free up the listener.
            self.state = 'processing'
            solvingProc = threading.Thread(target=self.Threaded_ask_all, args = [message, content, fn])
            solvingProc.start()

    def ask_one(self, conn, message):
        [fn, content] = self.ask_fn_content(conn, message)
        if fn in pythonian.quick_queries: 
            self.openSocket_ask_one(message, conn, content, fn) ## not in its own thread
        else: 
            conn.close() ## close the old connection; free up the listener.
            self.state = 'processing'
            solvingProc = threading.Thread(target=self.Threaded_ask_one, args = [message, content, fn])
            solvingProc.start()

    def answer_ask_all(self, message, content, fn):
        args = [self] #all functions must be called with agent as first argument
        unbounds = []
        for v in content[1:]:
            if v[0] == '?': unbounds.append(v)
            else: args.append(v)
        results = fn(*args) ## call the function with the arguments
        results = [stripQuotes(i) for i in results] ## this just strips extra quotes if they exist off the result values
        #print("our result is: " + str(result) + " and its type is: " + str(type(result)))
        return [args, results]
    
    def respond_ask_all(self, args, message, content, results):
##        if 'response' in message.keys() and message['response'] == ':pattern': ### ask all should never ask for a pattern, just bindings
##        #build the return s-expression
##            returnable = content[:len(args)]
##            if type(result) == list: returnable.extend(result)
##            else: returnable.append('"'+result+'"')
##            returnable = "(" + " ".join([str(i) for i in returnable]) + ")"
        if 'response' in message.keys() and message['response'] == ':bindings':
            ### gotta do some work to make them binding lists
            variables = content[len(args):] # get a list of variables
            returnable = [['('+str(var) + ' . ' + '"' +str(results[variables.index(var)]) + '"' + ')' for var in variables] for result in results] # make a list of binding lists
            returnable = ['(' + ' '.join([i for i in x]) + ')' for x in returnable] # format each list of binding lists so they're lisp lists, not python ones
            returnable = "(" + " ".join([str(i) for i in returnable]) + ")" # format them all together into one big binding list
        else: ## assume you want the expression
            #build the return s-expression
            # this should NEVER HAPPEN
            returnable = content[:len(args)]
            if type(results) == list: returnable.extend(results[0]) # just take the first one DO NOT DO THIS
            else: returnable.append('"'+results+'"')
            returnable = "(" + " ".join([str(i) for i in returnable]) + ")"

        # store the answer in a variable called reply.  
        # make sure you use the reply-with of the message id!
        reply = self.makeKQML(returnable, 
                              performative = "tell", 
                              send_to=message['sender'], 
                              reply_to=message['reply-with'])
        print(reply)
        return reply

    def respond_ask_one(self, args, message, content, results):
        result = results[0] # just take the first one
        if 'response' in message.keys() and message['response'] == ':pattern':
        #build the return s-expression
            returnable = content[:len(args)]
            if type(result) == list: returnable.extend(result)
            else: returnable.append('"'+result+'"')
            returnable = "(" + " ".join([str(i) for i in returnable]) + ")"
        elif 'response' in message.keys() and message['response'] == ':bindings':
            variables = content[len(args):]
            returnable = ['('+str(var) + ' . ' + '"' +str(result[variables.index(var)]) + '"' + ')' for var in variables]
            returnable = "((" + " ".join([str(i) for i in returnable]) + "))"
        else: ## assume you want the expression
            #build the return s-expression
            returnable = content[:len(args)]
            if type(result) == list: returnable.extend(result)
            else: returnable.append('"'+result+'"')
            returnable = "(" + " ".join([str(i) for i in returnable]) + ")"

        # store the answer in a variable called reply.  
        # make sure you use the reply-with of the message id!
        reply = self.makeKQML(returnable, 
                              performative = "tell", 
                              send_to=message['sender'], 
                              reply_to=message['reply-with'])
        print(reply)
        return reply

    def openSocket_ask_all(self, message, conn, content, fn):
        # just answer over the open socket
        [args, results] = self.answer_ask_all(message, content, fn)
        reply = self.respond_ask_all(args, message, content, results)
        self.conn.send(reply)
        ## close the connection to free up the listener
        self.conn.close()    
        
    def Threaded_ask_all(self, message, content, fn):
        ## this is the ask-all function that runs in its own thread; the listener connection has already been closed
        [args, results] = self.answer_ask_all(message, content, fn)
        reply = self.respond_ask_all(args, message, content, results)
        
        ## once you have the answer, open a new connection and reply.
        self.talkSoc = socket.socket()
        self.talkSoc.connect((self.facAdress, self.facPort))
        self.talkSoc.send(reply)
        self.talkSoc.close()    
        
        self.state = 'idle'

    def openSocket_ask_one(self, message, conn, content, fn):
        # just answer over the open socket
        [args, results] = self.answer_ask_all(message, content, fn) # still getting all the answers
        reply = self.respond_ask_one(args, message, content, results) ## just send one back
        self.conn.send(reply)
        ## close the connection to free up the listener
        self.conn.close()    
        
    def Threaded_ask_one(self, message, content, fn):
        ## this is the ask-all function that runs in its own thread; the listener connection has already been closed
        [args, results] = self.answer_ask_all(message, content, fn) # still getting all the answers
        reply = self.respond_ask_one(args, message, content, results) ## just send one back
        
        ## once you have the answer, open a new connection and reply.
        self.talkSoc = socket.socket()
        self.talkSoc.connect((self.facAdress, self.facPort))
        self.talkSoc.send(reply)
        self.talkSoc.close()    
        
        self.state = 'idle'

    ## to add to the list of things the beast can do
    ## has to be a string
    def addQuery(self, query):
        self.possibleQueries,append(query)

    def addQueries(self, queries):
        ## queries has to be a list of strings
        for query in queries: addQuery(query)

    def makeKQML(self, content, performative = "tell", send_to="facilitator", reply_to="nil"):
        msg = "("+ performative + " :sender " + self.name + \
            " :receiver " + send_to + " :in-reply-to " + reply_to + \
            " :reply-with " + str(self.messageCounter) + \
            " :content " + content + ")"
        self.messageCounter += 1
        return msg

    def register_function(self, signature, fn):
        self.fns[signature] = fn


def stripQuotes(listOfStrings):
    return [i[1:-1] if i.startswith('"') and i.endswith('"') else i for i in listOfStrings]

def main(argv):
    # get command line arguments.
    arg_parser = argparse.ArgumentParser(description='Starts up pythonian agent')
    
    arg_parser.add_argument('-facAdress', action="store", dest='facAdress', default='127.0.0.1')
    arg_parser.add_argument('-facPort', action="store", dest='facPort', default=9000, type=int)
    arg_parser.add_argument('-pyPort', action="store", dest='pyPort', default=8090, type=int)
    
    results = arg_parser.parse_args(argv)
    
    # launch agent
    pythag = pythonian(results.facAdress, results.facPort, results.pyPort)
    print("pythonian agent started")
    
if __name__ == "__main__":
    main(sys.argv[1:])

    