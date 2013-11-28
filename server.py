import SocketServer
import SimpleHTTPServer
from electrum import bitcoin
from decimal import Decimal
import bitcointools
import datetime
PORT = 8005

bitcoin_manager = bitcointools.BitcoinManager()

class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        #Sample values in self for URL: http://localhost:8080/jsxmlrpc-0.3/
        #self.path  '/jsxmlrpc-0.3/'
        #self.raw_requestline   'GET /jsxmlrpc-0.3/ HTTP/1.1rn'
        #self.client_address    ('127.0.0.1', 3727)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        if self.path.startswith('/check/'):#=='/move':
            file_hash = self.path[7:]
    	    print "Checking hash: " + str(file_hash)
            address = bitcointools.makeAddressFromData(file_hash)
    	    print "Checking address: " + str(address)
            if(bitcoin.is_valid(address)):
                print "Address is valid"
                address_history = bitcoin_manager.get_address_history(address)
                sorted_address_history = sorted(address_history, key = lambda x : x['height'])
                if(len(address_history) == 0):
                    print "Address has no history."
                    self.wfile.write("{\"exists\": false}")
                else:
                    first_transaction = sorted_address_history[0]
                    txid = first_transaction['tx_hash']
                    height = first_transaction['height']
                    print "Address has history with height, txid" + str((height, txid))
                    timestamp = bitcoin_manager.get_block_timestamp(height)
                    print "Timestamp: " + str(timestamp)
                    date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    print "Date: " + str(date)
                    if height > 1:
                        self.wfile.write("{\"exists\": true, \"date\": \"" + str(date) + "\"}")
                    else:
                        self.wfile.write("{\"exists\": true, \"date\": \"unconfirmed\"}")
            else:
                print "Invalid address"
                self.wfile.write("Invalid address")
        elif self.path.startswith('/commit/'):
            file_hash = self.path[8:]
            address = bitcointools.makeAddressFromData(file_hash)
	    print "Committing hash " + str(file_hash)
	    print "Committing address" + str(address)
            if(bitcoin.is_valid(address)):
                print "Address is valid"
                address_history = bitcoin_manager.get_address_history(address)
                if(len(address_history) > 0):
                    print "Address already in blockchain"
                    self.wfile.write("{\"success\": true}")
                else:#We actually have to commit it to the blockchain
                    print "Adding to blockchain"
                    try:
                    	if Decimal(bitcoin_manager.get_balance()['confirmed']) < Decimal('.0005'): #A little wiggle room
                    		raise Exception("Not enough funds in wallet")
                        txid = bitcoin_manager.send_money(address, Decimal(".0001"))
                    except Exception as e:
                        print "Error. Could not send money to address " + address + "."
                        print e
                        self.wfile.write("{\"success\": false}") 
                        return                   
                    self.wfile.write("{\"success\": true, \"txid\", \"" + str(txid) +   "\"}")
        else:
            print "invalid url"
            self.wfile.write("Invalid URL")



        

httpd = SocketServer.ThreadingTCPServer(('localhost', PORT),CustomHandler)

print "serving at port", PORT
httpd.serve_forever()
