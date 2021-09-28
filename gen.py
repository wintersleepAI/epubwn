from posixpath import join
from bs4 import BeautifulSoup, element
import sys
from os import path
import csv 


class ExtTable:
    def __init__(self, id, rows, attrs = None, name=None, inferred_parent=None):
        self.id = id
        self.rows = rows
        self.attr = attrs
        self.name = name
        self.inferred_parent=inferred_parent
    
    def __str__(self):
        return "id:%s attr:%s rows: %s name:%s parent: %s first 2:\n %s" % (self.id, self.attr, len(self.rows), self.name, self.inferred_parent, self.rows[:2])

    def get(id, html_soup):
        html_id = "table%s" %id 
        tt = html_soup.find(id=html_id)
        if tt:
            return extract_table(tt)
        else:
            raise LookupError("ID not found")

def write_res_to_csv(res, out_dir):
    for x in res:
        try:
            fn = "%s-%s-%s" % (x.id,x.name,x.inferred_parent)
            with open(path.join(out_dir,fn), 'w')  as output_file:
                dict_writer = csv.DictWriter(output_file, x.attr)
                dict_writer.writeheader()
                dict_writer.writerows(x.rows) 
        except Exception as e:
            print(e)

def print_table(h,t):
    if h is not None:
        print('\t\t'.join(h))
        for r in t:
            line = '\t\t'.join([r[x] for x in h])
            print(line)

def get_tables(filename, stop_at=None):
    with open(filename, "r") as infile:
        html = BeautifulSoup(infile.read(), "html.parser")
        tables = html.find_all('table')
        skipping = 0
        res = []
        for t in tables:
            try:
                if 'Basic-Table' not in t.get('class'):
                    ext_table = extract_table(t, html)
                    if len(ext_table.rows) > 1:
                        print("%s-%30s-%30s-%s " % (ext_table.id, ext_table.name, ext_table.inferred_parent, ext_table.attr))
                        res.append(ext_table)
                    else:
                        print("Skipping singleton %s" % ext_table.id)
                        skipping+=1
                else: 
                    pass
                    #print("Skipping simple %s" % t.get("id"))
                if stop_at and t.get("id") == stop_at:
                        print("Stopping early")
                        break

            except:
                print("skipping %s" %t.get("id"))
                skipping+=1
        
        print("Skipped: %s " % skipping)
        write_res_to_csv(res,"out")
        return res


def get_prior_id(id, split_word="_idContainer",zero_pad=3):
    """Take an id name and return the prior one"""
    if split_word not in id:
        return None
    str_id = id.split(split_word)[1]
    try:
        new_id = int(str_id)-1
        if new_id <= 0:
            return None
        return "%s%s" % (split_word, str(new_id).zfill(zero_pad))
    except Exception as e:
        print("Error getting prior ID %s" %  e)
        return None

def debug():
    fn = "WorldsWithoutNumber_EPUB_031521.xhtml"
    html = BeautifulSoup(open(fn, 'r').read(), 'html.parser')
    t = html.find(id="table506")
    et = extract_table(t, html)


#minor class="Header-Styles_Section-Header-Left"
def find_table_parent_title(table, html_soup):
    """Take a table and find the right parent title. If a minor
    section, keep looking for the parent major section"""
    title, ttype = get_inferred_title(table.parent)
    div_id = table.parent.get('id')
    if not ttype:
        # We have no title from the parent. Need to look going backwards
        div_id = get_prior_id(div_id)
        while div_id != None:
            elem = html_soup.find(id=div_id)
            if elem:
                title, ttype = get_inferred_title(elem)
                if ttype:
                    #We found a prior type we can stop
                    break
                else:
                    div_id = get_prior_id(div_id)
            else:
                print("Could not find %s"% div_id)
                break
                

    if ttype == 'Major':
        return title
    elif ttype == 'Minor' :
        div_id =  get_prior_id(div_id)
        while div_id != None:
            #print("looking for %s" %div_id)
            elem = html_soup.find(id=div_id)
            if elem:
                ptitle, ptype = get_inferred_title(elem)
                #print("found %s %s" % (ptitle, ptype))
                if ptype == 'Major':
                    return "%s-%s" % (ptitle,title)
                else:
                    div_id = get_prior_id(div_id)
            else:
                div_id = None
        #none found
        return "NA-%s" % title
    else:
        return None

     
def get_inferred_title(elem):
    """Look at the first p elements class for a Header word.
    If this is found, we assume the text in the elem is the title
    Retrun the type based on the class"""
    #print(elem)
    p = elem.find('p')
    if p:
        cls = p.get('class')
        #print(cls)
        hdr_cls = None
        for x in cls:
            if 'Header' in x:
                hdr_cls = x
        
        if hdr_cls:
            text = p.text
            #print(text)
            if 'Minor' in hdr_cls or hdr_cls.endswith('-Header-Left'):
                return (text, 'Minor')
            elif 'Major' in hdr_cls:
                return (text, 'Major')
            
    return None, None

def extract_table(table, html_soup=None):
    """Build an Extracted Table from a bs4 soup table tag.
    This will contain the id, rows, optional header attributes for the
    table (eg a header per column), and an
    optional name for the table (eg a single header row)"""
    res = []
    header = []
    name = None
    id = table.get('id')
    #print("Extracting table %s"% id)
    if not table.find('thead'):
        header = None
    else:
        for row in table.find('thead').find_all('tr'):
            is_header = True
            for cell in row.find_all('td'):
                if cell.get('colspan'):
                    is_header = False
                    if cell.find('p'):
                        p = cell.find('p')  
                        if 'Table-Styles_Table-Header-Major' in p.get('class'):
                            name  = p.text
                if is_header:            
                    header.append(cell.text.strip())
    for row in table.find('tbody').find_all('tr'):
        entry = {}
        for i, cell in enumerate(row.find_all('td')):
            if cell.get('rowspan'):
                raise Exception("Cannot handle rowspan")
            #print(cell)
            #print(cell.text)
            #c = ' '.join([str(' '.join(x.contents)) for x in cell.find_all('p')])
            if header:
                entry[header[i]] = cell.text.strip().replace('\n',' ')
            else:
                entry[i] = cell.text.strip().replace('\n',' ')
        res.append(entry)
    if html_soup:
        section_name = find_table_parent_title(table, html_soup)
    return ExtTable(id, res, header, name, section_name)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error, expected [epub html filename]")
        #sys.exit(2)
        debug()
    else:
        filename = sys.argv[1]
        stop = None
        if len(sys.argv) > 2:
            stop = "table%s"% str(sys.argv[2]).zfill(3)
            print("Stopping at %s" %stop)
        
        if not path.exists(filename):
            print("Error %s is not a valide file" % filename)
        else:
            get_tables(filename, stop)
