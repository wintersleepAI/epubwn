from posixpath import join
from bs4 import BeautifulSoup, element
import sys
from os import path


def print_table(h,t):
    if h is not None:
        print('\t\t'.join(h))
        for r in t:
            line = '\t\t'.join([r[x] for x in h])
            print(line)

def get_tables(filename):
    with open(filename, "r") as infile:
        html = BeautifulSoup(infile.read(), "html.parser")
        tables = html.find_all('table')
        skipping = 0
        res = []
        for t in tables:
            try:
                header, dict_table = extract_table(t)
                if len(dict_table) > 1:
                    res.append((header,dict_table))
            except:
                skipping+=1
        
        print(skipping)
        return res

def extract_table(table):
    res = []
    header = []
    if not table.find('thead'):
        header = None
    else:
        for cell in table.find('thead').find('tr').find_all('td'):
            
            #content = ' '.join([str(x.contents) for x in cell.find_all('p')])
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
    return (header, res) 



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error, expected [epub html filename]")
        sys.exit(2)
    else:
        filename = sys.argv[1]
        if not path.exists(filename):
            print("Error %s is not a valide file" % filename)
        else:
            get_tables(filename)