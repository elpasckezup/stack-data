from templateframework.metadata import Metadata
        
def run(metadata: Metadata = None):
    print(metadata.inputs)
    return metadata