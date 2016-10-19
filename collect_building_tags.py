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

def building_value(element, vals):
    if element.tag == "tag":
        elat=element.attrib
        elat_k=elat["k"]
        elat_v=elat["v"]
        if (elat_k=="building"):
            if elat_v not in vals:
                vals[elat_v]=1
            else:
                vals[elat_v]+=1
        
    return vals

def process_map(filename):
    vals = {}
    for _, element in ET.iterparse(filename):
        vals = building_value(element, vals)

    return vals

pprint.pprint(process_map(the_filename))
