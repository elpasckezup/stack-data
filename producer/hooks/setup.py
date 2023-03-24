import os
import sys
import yaml
import shutil
import questionary

from pathlib import Path
from templateframework.metadata import Metadata

def ask(data: dict):
    if 'plugins' in data:
        # required plugins
        required = list(filter(lambda plugin: plugin['required'], data['plugins']))
        if required:
            for plugin in required:
                ask(data=plugin)
        # optional plugins
        optional = list(filter(lambda plugin: not plugin['required'], data['plugins']))
        if optional:
            name = data.get('title', 'Stack')
            choices = [questionary.Choice(title=plugin['title'], value=plugin['name']) for plugin in optional ]
            choices.append(questionary.Separator(line='-'*30))
            choices.append(questionary.Choice(title='Select none', value='none'))
            answers = questionary.checkbox(message=f'Select optional [{name}] capabilities', choices=choices).unsafe_ask()
            if answers:
                if 'none' in answers:
                    for plugin in optional:
                        data['plugins'].remove(plugin)
                else:
                    unselected = list(filter(lambda plugin: plugin['name'] not in answers, optional))
                    if unselected:
                        for plugin in unselected:
                            data['plugins'].remove(plugin)

def start(metadata: Metadata):
    data = yaml.safe_load(Path(f'{metadata.component_path}/config/setup.yaml').read_text())
    ask(data=data)
    metadata.global_inputs['capabilities'] = []
    if 'plugins' in data:
        for plugin in data['plugins']:    
            apply(plugin=plugin, metadata=metadata)

def apply(plugin: dict, metadata: Metadata):
    metadata.global_inputs['capabilities'].append(plugin['name'])
    if 'plugins' in plugin:
        for child in plugin['plugins']:
            apply(plugin=child, metadata=metadata)
        
def run(metadata: Metadata = None):
    try:
        start(metadata=metadata)
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
            stack = os.path.basename(metadata.stack_path)
            for capability in metadata.global_inputs['capabilities']:
                os.system(f'cd {metadata.target_path} && stk apply plugin -p {metadata.stack_path}/{capability} --skip-warning')
        return metadata
    except KeyboardInterrupt:
        shutil.rmtree(metadata.target_path)
        sys.exit()