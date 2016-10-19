import xml.etree.cElementTree as ET
import pprint
import re
import sys

the_filename=str(sys.argv[1])

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
lower_double_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*:([a-z]|_)*$')
lower_with_dash = re.compile(r'^([a-z]|_|-)*$')
lower_colon_with_dash = re.compile(r'^([a-z]|_|-)*:([a-z]|_|-)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    if element.tag == "tag":
        elat=element.attrib
        elat_k=elat["k"]
        if problemchars.search(elat_k):
            keys["problemchars"]+=1
            #print("bad record")
            #print ("")
            #pprint.pprint(elat)
            #print("")
        elif (elat_k=="FIXME"):
            keys["FIXME"]+=1
        elif lower_colon.match(elat_k):
            keys["lower_colon"]+=1
        elif lower_double_colon.match(elat_k):
           keys["lower_double_colon"]+=1
        elif lower.match(elat_k):
            keys["lower"]+=1
        elif lower_with_dash.match(elat_k):
            keys["lower_with_dash"]+=1
        elif lower_colon_with_dash.match(elat_k):
            keys["lower_colon_with_dash"]+=1
        elif isinstance(elat_k, unicode):
            keys["unicode"]+=1
        else:
            #print("weird record")
            #print ("")
            #pprint.pprint(elat)
            #print(elat)
            #print("")
            keys["other"]+=1
        pass
        
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "lower_double_colon":0,  "lower_with_dash":0,  "lower_colon_with_dash":0, "problemchars": 0, "FIXME":0, "unicode":0,   "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

pprint.pprint(process_map(the_filename))
