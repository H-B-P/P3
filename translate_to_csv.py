
import csv
import codecs
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "beijing_china.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"

WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

RELATIONS_PATH = "relations.csv"
RELATION_MEMBERS_PATH = "relations_members.csv"
RELATION_TAGS_PATH = "relations_tags.csv"


LOWER_COLON = re.compile(r'^([a-z]|_|-)+:([a-z]|_|-)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['tagid', 'id', 'key', 'value', 'type']

WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['tagid', 'id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['thisid', 'id', 'node_id', 'position']

RELATION_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
RELATION_TAGS_FIELDS = ['tagid','id', 'key', 'value', 'type']
RELATION_MEMBERS_FIELDS = ['thisid','id', 'member_id', 'role', 'type']

#Set up an int to assign a primary key to everything which doesn't have a natural one.
PRIMARY_KEY_INT=70000

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""
    
    global PRIMARY_KEY_INT
    
    #Set up empty dicts and arrays.
    
    node_attribs = {}
    way_attribs = {}
    relation_attribs={}
    relation_members=[]
    way_nodes = []
    tags = [] 
    
    #If the element is a node, add all the content.
    
    if element.tag=='node':
        for n_f in NODE_FIELDS:
            if n_f in element.attrib:
                node_attribs[n_f]=element.attrib[n_f]
    
    #If the element is a way, add all the content.
    
    if element.tag=='way':
        for w_f in WAY_FIELDS:
            if w_f in element.attrib:
                way_attribs[w_f]=element.attrib[w_f]
        
        #Also add an entry for every node associated with the way.
        
        nodelist=element.findall("nd")
        numb=0
        for listed_node in nodelist:
            entry={}
            entry["id"]=element.attrib["id"]
            entry["node_id"]=listed_node.attrib["ref"]
            entry["position"]=numb
            
            #In addition to the keys associated with the way and the node, the tag which connects them is given its own primary key.
            entry["thisid"]=PRIMARY_KEY_INT
            #Increment after each assignment to ensure uniqueness.
            PRIMARY_KEY_INT+=1
            numb+=1
            way_nodes.append(entry)
            
        
    
    #If the element is a relation, add all the content.
    
    if element.tag=='relation':
        for r_f in RELATION_FIELDS:
            if r_f in element.attrib:
                relation_attribs[r_f]=element.attrib[r_f]
        
        #Also add an entry for every way associated with the relation.
        
        memberlist=element.findall("member")
        for listed_member in memberlist:
            entry={}
            entry["id"]=element.attrib["id"]
            entry["member_id"]=listed_member.attrib["ref"]
            entry["role"]=listed_member.attrib["role"]
            entry["type"]=listed_member.attrib["type"]
            
            #In addition to the keys associated with the way and the node, the tag which connects them is given its own primary key.
            entry["thisid"]=PRIMARY_KEY_INT
            #Increment after each assignment to ensure uniqueness.
            PRIMARY_KEY_INT+=1
            
            #Members can include ways or nodes, but we only want the ways.
            if entry["type"]=="way":
                relation_members.append(entry)
            
            
        
        
    
    
    taglist=element.findall("tag")
    
    #Before the main iteration through the tags, check whether there are building and amenity tags there, so we know whether to cross-pollinate them.
    
    amenity_listed=0
    building_listed=0
    for listed_tag in taglist:
        if listed_tag.attrib["k"]=="amenity":
            amenity_listed=1
        if listed_tag.attrib["k"]=="building":
            building_listed=1
    
    #Now the program actually iterates through tags.
    
    for listed_tag in taglist:
        
        #Deal with problematic tags identified earlier; print every time this happens so the user can check the right number of replacements occurred.
        
        if listed_tag.attrib["k"]=="No.":
            listed_tag.attrib["k"]="number"
            print ("No. -> Number")
        if " " in listed_tag.attrib["k"]:
            listed_tag.attrib["k"]=listed_tag.attrib["k"].replace(" ",  "_")
            print ("emergency shelter -> emergency_shelter")
        
        
        #Deal with problems found in the building and amenity values.
        
        purge_this=0
        
        #Convert all uppercase to lowercase.
        listed_tag.attrib["v"]=listed_tag.attrib["v"].lower()
        #Replace all dashes with underscores.
        listed_tag.attrib["v"]=listed_tag.attrib["v"].replace("-",  "_")
        #Replace all spaces with underscores.
        listed_tag.attrib["v"]=listed_tag.attrib["v"].replace(" ",  "_")
        
        #Replace any "yes" and "yesm" in the building tag with "unspecified".
        if listed_tag.attrib["k"]=="building":
            if listed_tag.attrib["v"]=="yes" or listed_tag.attrib["v"]=="yesm":
                listed_tag.attrib["v"]="unspecified"
        
        #Purge any value which has a number in it.
        for digit in [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]:
            if str(digit) in listed_tag.attrib["v"]:
                purge_this=1
        #Purge unicode, and for that matter all nonstrings. (note this only works in python 2.x)
        if not isinstance(listed_tag.attrib["v"], str):
            purge_this=1 
        
        #Append the tag, assuming it's nonproblematic and not marked for purging.
        
        if None==(PROBLEMCHARS.search(listed_tag.attrib["k"])) and None==(PROBLEMCHARS.search(listed_tag.attrib["v"])) and purge_this==0:
            entry={}
            entry["id"]=element.attrib["id"]
            entry["tagid"]=PRIMARY_KEY_INT
            PRIMARY_KEY_INT+=1
            entry["value"]=listed_tag.attrib["v"]
            
            #Split anything which begins with a colon.
            
            if ":" in listed_tag.attrib["k"]:
                #The key could have more than one colon: be sure to only split it once!
                key_parts=listed_tag.attrib["k"].split(":",1)
                entry["type"]=key_parts[0]
                entry["key"]=key_parts[1]
            
            else:
                entry["type"]=default_tag_type
                entry["key"]=listed_tag.attrib["k"]
            
            #Add tag.
            tags.append(entry.copy())
            
            #If only one of the amenity and building tags are on something, but it's a something counted as both a building and amenity (i.e. a college, university or hospital), add another tag
            if entry["key"]=="building" and amenity_listed<building_listed:
                if entry["value"]=="college" or entry["value"]=="hospital" or entry["value"]=="university":
                    other_entry=entry.copy()
                    other_entry["key"]="amenity"
                    other_entry["tagid"]=PRIMARY_KEY_INT
                    PRIMARY_KEY_INT+=1
                    tags.append(other_entry.copy())
            if entry["key"]=="amenity" and amenity_listed>building_listed:
                if entry["value"]=="college" or entry["value"]=="hospital" or entry["value"]=="university":
                    other_entry=entry.copy()
                    other_entry["key"]="building"
                    other_entry["tagid"]=PRIMARY_KEY_INT
                    PRIMARY_KEY_INT+=1
                    tags.append(other_entry.copy())
            
            
            
    
    #Finally, return objects.
    
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    elif element.tag == 'relation':
        return {'relation': relation_attribs, 'relation_members': relation_members, 'relation_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        print errors
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    
    
    
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file, \
         codecs.open(RELATIONS_PATH, 'w') as relations_file, \
         codecs.open(RELATION_MEMBERS_PATH, 'w') as relation_members_file, \
         codecs.open(RELATION_TAGS_PATH, 'w') as relation_tags_file:
        
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        
        relations_writer = UnicodeDictWriter(relations_file, RELATION_FIELDS)
        relation_members_writer = UnicodeDictWriter(relation_members_file, RELATION_MEMBERS_FIELDS)
        relation_tags_writer = UnicodeDictWriter(relation_tags_file, RELATION_TAGS_FIELDS)
        
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        
        relations_writer.writeheader()
        relation_members_writer.writeheader()
        relation_tags_writer.writeheader()
        
        validator = cerberus.Validator()
        
        for element in get_element(file_in, tags=('node', 'way',  'relation')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
                elif element.tag == 'relation':
                    relations_writer.writerow(el['relation'])
                    relation_members_writer.writerows(el['relation_members'])
                    relation_tags_writer.writerows(el['relation_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
