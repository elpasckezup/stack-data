import os
import sys
import yaml

from pathlib import Path
from templateframework.metadata import Metadata

class Dictionary:

    @staticmethod
    def apply(data: dict, path: str, value: any):
        leaf = data
        keys = path.split('.')
        attr = keys.pop()
        for key in keys:
            if key not in leaf:
                leaf[key] = {}
            leaf = leaf[key]
        leaf[attr] = value
    
    @staticmethod
    def extract(data: dict, path: str) -> any:
        leaf = data
        keys = path.split('.')
        attr = keys.pop()
        for key in keys:
            if key not in leaf:
                return None
            leaf = leaf[key]
        return leaf[attr] if attr in leaf else None 
    
    @staticmethod
    def has(data: dict, path: str) -> bool:
        return Dictionary.extract(data=data, path=path) is not None

def load(path: str) -> dict:
    data = yaml.safe_load(Path(path).read_text())
    return data

def append(root=dict, data=dict):
    kind = data['kind']
    spec = data['spec']
    if kind == 'Application':
        spec.update(data['metadata'])
        Dictionary.apply(data=root, path='application', value=spec)
    elif kind == 'Ingestion/Api':
        apis = Dictionary.extract(data=root, path='ingestion.apis')
        if apis == None:
            apis = []
            Dictionary.apply(data=root, path='ingestion.apis', value=apis)
        spec.update(data['metadata'])
        apis.append(spec)
    elif kind == 'Storage/S3':
        Dictionary.apply(data=root, path='storage.s3', value=spec)
    elif 'Ingestion/Source' in kind:
        sources = Dictionary.extract(data=root, path='ingestion.sources')
        if sources == None:
            sources = []
            Dictionary.apply(data=root, path='ingestion.sources', value=sources)
        spec['type'] = os.path.basename(kind)
        sources.append(spec)
    elif 'DataProduct/Discoverability' in kind:
        Dictionary.apply(data=root, path='dataproduct.discoverability', value=spec)
    elif 'DataProduct/DataSet' in kind:
        datasets = Dictionary.extract(data=root, path='dataproduct.datasets')
        if datasets == None:
            datasets = []
            Dictionary.apply(data=root, path='dataproduct.datasets', value=datasets)
        spec.update(data['metadata'])
        datasets.append(spec)

def start(workdir: str) -> dict:
    root = {}
    for path, folders, files in os.walk(workdir):
        for file in files:
            print(os.path.join(path, file))
            data = load(path=os.path.join(path, file))
            append(root=root, data=data)
    return root

def run(metadata: Metadata = None):
    data = start(workdir='./')
    metadata.global_inputs.update(data)
    with open(f'{metadata.target_path}/stk.yaml', 'w') as file:
        template = os.path.basename(metadata.component_path)
        data = {
            'stack_type': 'app',
            'applied_templates': [
                {
                    'inputs': metadata.inputs,
                    'template_data_path': f'/{template}'
                }
            ],
            'global_inputs': metadata.global_inputs,
            'global_computed_inputs': metadata.global_computed_inputs
        }
        yaml.dump(data, file)
    return metadata

#run(workdir=sys.argv[1])
