import json

import select
import socket

class ClientConnection:
    def parseAndExecute( self, cmd ):
        pass
    
    def close( self ):
        self.socket.close()

    def readAll( self ):
        ret = select.select( [self.socketfile], [], [], 0 )

        if( len( ret[0] ) > 0 ):
            l = self.socketfile.readline()
            decoded = json.loads( l )

            if( decoded.has_key('cmd') and decoded.has_key('data') ):
                cmd = decoded['cmd']
                data = decoded['data']
                print "COMMAND: %s with data %s" % (cmd, data)
                if cmd == "AUTH_RES":
                    self.state = "auth"

                if cmd == "JOIN_RES":
                    self.state = "join"

            if self.state == "auth":
                self.socket.sendall( '{"cmd":"JOIN_REQ", "data":{"token":"Cage"}}\r\n' )

            if self.state == "join":
                #self.socket.sendall( '{"cmd":"DBG_VIS", "data":{"match_token":"Cage"}}\r\n' )
                #self.socket.sendall( '{"cmd":"ABL_REQ", "data":{"abl_id":0,"tgt_pos":[0,0,0],"t":1}}\r\n' )
                #self.socket.sendall( '{"cmd":"BUILD_ACT_REQ", "data":{"s_id":2, "act_id":6}}\r\n' )
                self.state = "game"



    def __init__(self, host, port):
        self.hostname = host
        self.port = port
        self.state = "undef"

        self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.socket.connect( (self.hostname, self.port) )

        self.socketfile = self.socket.makefile()

        self.socket.sendall( '{"cmd":"AUTH", "data":{"user":"soiha2", "password":"bar"}}\r\n' )


def main( host = "localhost", port =  32073 ):
    c = ClientConnection( host, port )
    while True:
        try:
            c.readAll()
            cmd = "" #cmd = raw_input( "> " )
            if( cmd == "quit" or cmd == "q" ):
                c.close()
                break
            c.parseAndExecute( cmd )
        except( KeyboardInterrupt, SystemExit, EOFError ):
            c.close()
            print "\nQuit!"
            break

if __name__ == "__main__":
    main()
