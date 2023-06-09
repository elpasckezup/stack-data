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
        types = {
            'Ingestion/Source/S3': 'S3',
            'Ingestion/Source/RDS': 'RDS',
            'Ingestion/Source/DynamoDB': 'DYNAMO_DB'
        }
        spec['type'] = types[kind]
        sources = Dictionary.extract(data=root, path='ingestion.sources')
        if sources == None:
            sources = []
            Dictionary.apply(data=root, path='ingestion.sources', value=sources)
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

def pl(kind:str):

    return None

def start(workdir: str, plugins:list) -> tuple:
    root = {}
    plugins = []
    for path, folders, files in os.walk(workdir):
        for file in files:
            if file.endswith("yml") or file.endswith("yaml"):
                data = load(path=os.path.join(path, file))
                append(root=root, data=data)
                plugin = pl(kind=data['kind'])
                if plugin is not None:
                    if plugin not in plugins:
                        plugins.append(plugin)
    return (root, plugins)

def run(metadata: Metadata = None):
    data, plugins = start(workdir='./')
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
    path = metadata.target_path
    stack = os.path.basename(metadata.stack_path)
    for plugin in plugins:
        os.system(f'cd {path} && stk apply plugin {stack}/{plugin} --skip-warning')
    return metadata

#run(workdir=sys.argv[1])
