import xml.etree.cElementTree as ET
import pprint

def count_tags(filename):
        dyct = {}
        for event, elem in ET.iterparse(filename):
            elta=elem.tag
            #pprint.pprint(elta)
            if elta in dyct:
                dyct[elta]+=1
            else:
                dyct[elta]=1
        
        return dyct
        
pprint.pprint(count_tags("beijing_china.osm"))
