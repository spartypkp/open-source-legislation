import psycopg2
import utils.utilityFunctions as util
class Node:
    def __init__(self, node_id, node_parent, top_level_title, node_type, node_level_classifier,
                 node_text=None, node_citation=None, node_link=None,
                node_name=None, node_addendum=None, node_summary=None,
                 node_hyde=None, node_tags=None):
        
        self.node_id = node_id
        self.node_top_level_title = top_level_title
        self.node_type = node_type
        self.node_level_classifier = node_level_classifier
        self.node_text = node_text
        self.node_text_embedding = None
        self.node_citation = node_citation
        self.node_link = node_link
        self.node_addendum = node_addendum
        self.node_name = node_name
        self.node_name_embedding = None
        self.node_summary = node_summary
        self.node_summary_embedding = None
        self.node_hyde = node_hyde
        self.node_hyde_embedding = None
        self.node_parent = node_parent  # Refers to another Node instance
        self.node_direct_children = None
        self.node_siblings = None
        self.node_references = None
        self.node_incoming_references = None
        self.node_tags = node_tags
    def __str__(self):
        if (self.node_parent is None):
            parent = None
        else:
            parent = self.node_parent.node_id
        return f"Node: ({self.node_id}, {self.node_type}, {self.node_level_classifier}, {self.node_name},{parent}, {self.node_text}, {self.node_citation}, {self.node_link})\n"
    
    def get(self):
        if (self.node_parent is None):
            parent = None
        else:
            parent = self.node_parent.node_id
        return (self.node_id, self.node_top_level_title, self.node_type, self.node_level_classifier,self.node_text, self.node_text_embedding, self.node_citation, self.node_link,self.node_addendum, self.node_name, self.node_name_embedding, self.node_summary, self.node_summary_embedding,self.node_hyde, self.node_hyde_embedding, parent, self.node_direct_children, self.node_siblings,self.node_references, self.node_incoming_references, self.node_tags)
    
    def reset_id(self, number):
        node_id = f"{self.node_parent.node_id}{self.node_level_classifier}={number}/"
        self.node_id = node_id
    
    def insert(self, , TABLE_NAME, handle_duplicate_id="DEFAULT-ERROR"):
        row_data = self.get()
        if (handle_duplicate_id == "IGNORE"):
            try:
                util.insert_row_to_local_db(, TABLE_NAME, row_data)
                return True
            except psycopg2.errors.UniqueViolation as e:
                return False
            return
        elif (handle_duplicate_id == "FORCE-NEW-VERSION"):
            base_node_id = self.node_id
            new_version = False
            for i in range(2, 10):
                try:
                    util.insert_row_to_local_db(, TABLE_NAME, row_data)
                    return new_version
                except:
                    new_version = True
                    self.node_id = base_node_id + f"-v{i}/"
                    self.node_type = "content_duplicate"
                    row_data = self.get()
                continue
            
        else:
            util.insert_row_to_local_db(, TABLE_NAME, row_data)
            return True

    
