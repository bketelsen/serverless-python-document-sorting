import os
import glob
import boto3
import hashlib

# create a metadata structure for the document
class DocumentMetadata:
    def __init__(self, name, md5, entities, docdate, mainentity, documenttype,category,containspii):
        self.name = name
        self.md5 = md5
        self.entities = entities
        self.docdate = docdate
        self.mainentity = mainentity
        self.documenttype = documenttype
        self.category = category
        self.containspii = containspii

    def __str__(self):
        return self.name + " " + self.md5 + " " + self.entities + " " + self.docdate + " " + self.mainentity
    

    def pretty_print(self):
        pretty_output = """Name={}
MD5={}
Entities={}
DocumentDate={}
MainEntity={}
DocumentType={}
Category={}
ContainsPII={}
""".format(self.name, self.md5, self.entities, self.docdate, self.mainentity, self.documenttype, self.category, self.containspii)
        return pretty_output


    def save(self, file):
        with open(file, 'w') as f:
            f.write(self.pretty_print())
        f.close()

# get list of files in directory
def get_files():
    files = glob.glob("docs/*.pdf")
    return files

# iterate through textract response, printing the text
def get_text(response):
    result = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            result.append(item["Text"])
        if item["BlockType"] == "WORD":
            result.append(item["Text"])
    return result
        
# with boto3, use textract to analyze the document
def analyze_document(bytes):
    client = boto3.client('textract')
    response = client.analyze_document(
        Document={
            'Bytes': bytes
        },
        FeatureTypes=["TABLES", "FORMS"]
    )
    return response

# with boto3, use amazon comprehend to detect entities in the document
def detect_entities(str):
    client = boto3.client('comprehend')
    response = client.detect_entities(Text=str, LanguageCode='en')
    return response


# read the bytes of a file
def read_file(file):
    with open(file, 'rb') as f:
        return f.read()

# create an md5 hash of byte array
def md5_hash(bytes):
    return hashlib.md5(bytes).hexdigest()

def main():
    # iterate through list of files
    files = get_files()

    # create a dictionary of files and their md5 hashes
    md5_dict = {}
    duplicates = []

    for x in range (len(files)):
        # print each file name to the console
        print(files[x])

        bytes = read_file(files[x])
        filehash = md5_hash(bytes)
        if filehash in md5_dict:
            duplicates.append(files[x])
        else:

            # copy the file into the output directory
            # with the md5 hash as the file name
            os.system("cp "+ files[x] + " output/" + filehash + ".pdf")

            md5_dict[filehash] = files[x]
            response = analyze_document(bytes)
            # write response in a a json file
            with open("output/" + filehash + '.json', 'w') as f:
                f.write(str(response))
                f.close()
                result = get_text(response)
                if md5_hash(str(bytes).encode('utf-8')) in md5_dict:
                    duplicates.append(files[x])
                else:
                    md5_dict[md5_hash(str(bytes).encode('utf-8'))] = files[x]
                    # this is the list of entities in the document
                    detectresult = detect_entities(str(result))
                    with open("output/" + filehash + '.entities.txt', 'w') as f:
                        f.write(str(detectresult))
                    f.close()

                    firstdatefound = False
                    firstdate = ""

                    # iterate through the entities in the list, finding the first date
                    # with a confidence greater than 99%
                    for item in detectresult["Entities"]:
                        if item["Score"] > 0.99 and item["Type"] == "DATE":
                            firstdatefound = True
                            firstdate = item["Text"]
                            break

                    # if a date was found, print it to the console
                    if firstdatefound:
                        print("first date: " +firstdate)

                    # create a document metadata object
                    doc = DocumentMetadata(files[x], filehash, "", firstdate, "","","",False)
                    doc.save("output/" + filehash + '.metadata.txt')

    print("---------------------------------------------")
    print(duplicates)

if __name__ == "__main__":
    main()