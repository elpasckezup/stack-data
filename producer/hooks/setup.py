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
            answers = questionary.checkbox(message=f'Select optional [{name}] items', choices=choices).unsafe_ask()
            if answers:
                if 'none' in answers:
                    for plugin in optional:
                        data['plugins'].remove(plugin)
                else:
                    unselected = list(filter(lambda plugin: plugin['name'] not in answers, optional))
                    if unselected:
                        for plugin in unselected:
                            data['plugins'].remove(plugin)

def start(path: str):
    data = yaml.safe_load(Path(f'{path}/producer/config/setup.yaml').read_text())
    ask(data=data)
    if 'plugins' in data:
        for plugin in data['plugins']:    
            apply(path=path, plugin=plugin)

def apply(path: str, plugin: dict):
    name = plugin['name']
    os.system(f'stk apply plugin data/{name}')
    if 'plugins' in plugin:
        for child in plugin['plugins']:
            apply(path=path, plugin=child)
        
def run(metadata: Metadata = None):
    try:
        start(path=metadata.stack_path)
    except KeyboardInterrupt:
        shutil.rmtree(metadata.target_path)
        sys.exit()
