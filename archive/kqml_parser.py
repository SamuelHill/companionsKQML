import string 
from nltk.tokenize import regexp_tokenize
delimiters = '():' 
class KQMLsyntax(Exception):
    def __init___(self,dErrorArguments):
        Exception.__init__(self,"KQML Syntax Error:  {0}".format(dErrArguments))
        self.dErrorArguments = dErrorArguements

class KQMLmessage(dict):
    
    def __init__( self, msg = ""):  
        dict.__init__(self)
        self.performative = ""
        self.msg = msg
        if msg:
            self.parseMessage(msg)
            
    def __repr__( self):
        output = [] 
        if not self.keys(): return self.msg
        else:
            fields = self.keys()
            for field in fields:
                output.append(":%s" % field) 
                output.append( str( self[ field]))
            output.append(")")
            return str(output)

    getSendString = __repr__ 
    
    def getReadString( self, olddepth = 0): 
        output = [] 
        makesp = lambda n: ' ' * n 
        output.append("(%s\n" % self.performative) 
        depth = olddepth + len( self.performative) + 1 
        fields = self.keys() 
        fields.reverse() 
        for field in fields: 
            output.append("%s:%s " % ( makesp(depth), field)) 
            value = self[ field] 
            if hasattr( value, "performative"): 
                output.append( value.getReadString( depth + len( field) + 2)) 
            else: 
                output.append( str( self[ field])) 
            output.append( '\n') 
        output.append( makesp( olddepth) + ")") 
        return string.join( output, '') 
    
    def parseMessage( self, msg):
        #print("message: " + str(msg))
        tokens = regexp_tokenize(msg, pattern=':pattern|:bindings|"[^"]+"|[:()]|[\"a-zA-Z0-9\-\_\?\\\/\:\.\"]+') # have to put in keywords that shouldn't be split up, i.e., "bindings". "[^"]+" leaves quoted strings intact
        if ":" not in tokens: return
        elif tokens[0] != "(" and tokens[1] in delimiters: 
            raise KQMLsyntax({"Performative is missing"}) 
        else:
            self.performative = tokens[1] 
            self['performative'] = self.performative
            pos = 2 
            while pos < len( tokens): 
                token = tokens[pos] 
                if token == ":": 
                    field = tokens[pos + 1] 
                    if tokens[pos + 2] == "(": 
					## I just realized this will have problems with nested parens because
					## it stops when it hits the FIRST close paren.
                        next_pos = pos + 3 
                        while tokens[ next_pos] != ")": 
                            next_pos += 1
                        msg2 = "("+" ".join( tokens[ pos+3: next_pos]) + ")"
                        value = KQMLmessage(msg2) 
                        pos = next_pos + 1 
                    else: 
                        value = tokens[pos + 2] 
                        pos = pos + 3 
                    self[ field] = value 
                elif token == ")": 
                    break 
                else: 
                    raise KQMLsyntax({"Expected a field, got: ", str(tokens[pos])})
    
    #def _tokenize( self, kqml_string): 
    #    tokens = [] 
    #    pos = 0 
    #    while pos < len( kqml_string): 
    #        c = kqml_string[ pos] 
    #        if c in delimiters: 
    #            tokens.append( c) 
    #            pos = pos + 1 
    #        elif c == '"': 
    #            next_pos = string.find( kqml_string, '"', pos + 1) 
    #            if next_pos == -1: 
    #                raise KQMLsyntax("Bad string")
    #            tokens.append( kqml_string[pos:next_pos+1]) 
    #            pos = next_pos + 1 
    #        elif c not in string.whitespace: 
    #            word = [] 
    #            for c in kqml_string[pos:]: 
    #                if c in string.whitespace: break 
    #                word.append(c) 
    #            word = string.join( word, '') 
    #            tokens.append( word) 
    #            pos = pos + len(word) 
    #        else: 
    #            pos = pos + 1 
    #    return tokens 

def test(): 
    kqml = """(tell      :sender joe 
        :receiver jed 
        :command (load-agent :agentname Moulder 
                             :agentdata (function :defa 1 
                                                  :defb 10 
                                                  :code "lambda x,y: x+y")) 
)""" 
