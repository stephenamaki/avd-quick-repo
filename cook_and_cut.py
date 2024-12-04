#!/usr/bin/env python3

import json
import yaml
import csv
from cookiecutter.main import cookiecutter
import os
import sys
import argparse

def read_yaml_file(filename, load_all=False):
    with open(filename, mode='r') as f:
        if not load_all:
            yaml_data = yaml.load(f, Loader=yaml.FullLoader)
        else:
            # convert generator to list before returning
            yaml_data = list(yaml.load_all(f, Loader=yaml.FullLoader))
    return yaml_data

def read_csv_file(filename):
    with open(filename, mode='r') as csv_file:
        csv_row_dict_list = list()  # list of key-value pairs produced from every CSV row except header
        # if header contains __CCvar and __CCvalue CSV will be processed vertically
        # each row will be treated as separate variable with a name of __CCvar
        vars_from_csv = dict()
        for row in csv.DictReader(csv_file):
            updated_row_dict = dict()
            for k, v in row.items():
                # remove potential spaces left and right
                k = k.strip()
                if v:
                    v = v.strip()
                updated_row_dict.update({k: v})
            if '__CCkey' in updated_row_dict.keys():
                if not '__CCvalue' in updated_row_dict.keys():
                    sys.exit(
                        f'ERROR: __CCkey is defined without __CCvalue in {csv_file}')
                vars_from_csv.update({updated_row_dict['__CCkey']: updated_row_dict['__CCvalue']})
            else:
                csv_row_dict_list.append(updated_row_dict)

    if len(csv_row_dict_list):
        return csv_row_dict_list
    else:
        return vars_from_csv
    

class Cut:

    def __init__(self, data_input_directory) -> None:
        # init cookiecutter dict
        # in/out keys help to split processed and unprocessed data
        # and add another nesting level required for lists in cookiecutter.json to work
        self.cookiecutter_vars = {
            'in': dict(),  # unprocessed input data
            'out': dict(),  # processed output data
            # copy real jinja2 templates without rendering
            '_copy_without_render': [
                '*.j2'
            ]
        }
    
        # load all data from input directory and assign to corresponding dict keys
        data_input_directory_full_path = os.path.join(
            os.getcwd(), data_input_directory)
        if not os.path.isdir(data_input_directory_full_path):
            sys.exit(
                f'ERROR: Can not find data input directory {data_input_directory_full_path}')
            
        # read files from the data input directory and add data to cookiecutter json
        # every file will be added as dictionary with a filename without extension as the parent key
        for a_name in os.listdir(data_input_directory_full_path):
            a_full_path = os.path.join(data_input_directory_full_path, a_name)
            if os.path.isfile(a_full_path):
                if '.csv' in a_name.lower():
                    csv_data = read_csv_file(a_full_path)
                    
                    self.cookiecutter_vars['in'].update({
                        # [:-4] removes .csv
                        a_name.lower()[:-4]: csv_data
                    })
                elif '.yml' in a_name.lower():
                    data_from_yaml = read_yaml_file(a_full_path)
                    self.cookiecutter_vars['in'].update({
                        # [:-4] removes .yml
                        a_name.lower()[:-4]: data_from_yaml
                    })
                elif '.yaml' in a_name.lower():
                    data_from_yaml = read_yaml_file(a_full_path)
                    self.cookiecutter_vars['in'].update({
                        # [:-5] removes .yaml
                        a_name.lower()[:-5]: data_from_yaml
                    })

    def cut(self, cookiecutter_template_directory, cookiecutter_output_dir='.'):
        if not os.path.isdir(cookiecutter_template_directory):
            # if no fullpath specified, build fullpath from cwd
            cookiecutter_template_directory = os.path.join(
                os.getcwd(), cookiecutter_template_directory)
            if not os.path.isdir(cookiecutter_template_directory):
                # log error and exit if specified template directory is not present in cwd
                sys.exit(
                    f'ERROR: cant find cookiecutter template directory {cookiecutter_template_directory}')
        # write cookiecutter.json
        cookiecutter_json_filename = os.path.join(
            cookiecutter_template_directory, 'cookiecutter.json')
        with open(cookiecutter_json_filename, 'w') as cc_json_file:
            json.dump(self.cookiecutter_vars, cc_json_file, indent=4)
        # run cookiecutter to build output data
        cookiecutter(cookiecutter_template_directory, no_input=True,
                    overwrite_if_exists=True, output_dir=cookiecutter_output_dir)
        
if __name__ == "__main__":

    # Get cookiecutter output_directory from CLI argument or default
    parser = argparse.ArgumentParser(
        prog="Cook-and-cut",
        description="This script creates expanded data from cookiecutter templates.")
    parser.add_argument(
        '-in', '--input_directory', default='CSVs',
        help='Directory to keep the AVD repository produced by cookiecutter'
    )
    parser.add_argument(
        '-out', '--output_directory', default='.',
        help='Directory to keep the AVD repository produced by cookiecutter'
    )
    parser.add_argument(
        '-td', '--template_dir', default='.cc',
        help="Cookiecutter template directory"
    )
    args = parser.parse_args()

    cc = Cut(args.input_directory)
    cc.cut(args.template_dir)
