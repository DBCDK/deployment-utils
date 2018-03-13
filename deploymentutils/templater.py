#!/usr/bin/env python3
# Copyright Dansk Bibliotekscenter a/s. Licensed under GPLv3
# See license text at https://opensource.dbc.dk/licenses/gpl-3.0

import argparse
import configparser
import copy
import fnmatch
import os
import sys

class ConfigException(Exception):
    pass

class StoreTemplateKeyValuePairsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if self.nargs is None:
            values = [values]
        for value in values:
            try:
                key, value = value.split("=")
                if getattr(namespace, self.dest) is None:
                    setattr(namespace, self.dest, {})
                getattr(namespace, self.dest)[key] = value
            except ValueError as e:
                setattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR, value)

def setup_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input",
        help="templated file or directory of files to fill")
    parser.add_argument("--output-dir",
        help="directory to write resulting files to")
    parser.add_argument("--template-keys", nargs="+",
        action=StoreTemplateKeyValuePairsAction,
        help="templated keys to replace with a given value. "
        "e.g. `--template-keys key=value` will replace ${key} with value",
        default={})
    parser.add_argument("--template-keys-file", help="read template keys "
        "from file in key=value format. template keys specified on the "
        "command line takes precedence over those specified in a file")
    parser.add_argument("--exclude", help="pattern for files to exclude, "
        "accepts * and ? as wildcards")
    parser.add_argument("--include", help="pattern for files to include, "
        "accepts * and ? as wildcards")
    parser.add_argument("--separator",
        help="string for separating multiple config files printed to stdout, "
        "defaults to --- (separating yaml files)", default="---")
    args = parser.parse_args()
    return args

def fill_template(template, **kwargs):
    for key, value in kwargs.items():
        # replace ${key} -> value
        template = template.replace("${{{}}}".format(key), value)
    return template

def read_template_keys_file(path):
    try:
        with open(path) as template_keys_file:
            # put in a section because configparser expects that
            template_keys = "[default]\n" + template_keys_file.read()
            parser = configparser.ConfigParser()
            # make sure configparser doesn't lower-case values
            parser.optionxform = str
            parser.read_string(template_keys)
            return {key: value for key, value in parser["default"].items()}
    except (IOError, configparser.ParsingError)  as e:
        raise ConfigException("error parsing template keys file", e)

def merge_template_keys(file_path, template_keys_from_args):
    template_keys = {}
    if template_keys_from_args is not None:
        template_keys = copy.deepcopy(template_keys_from_args)
    template_keys_from_file = read_template_keys_file(file_path)
    for key in template_keys_from_file:
        if key not in template_keys:
            template_keys[key] = template_keys_from_file[key]
    return template_keys

def iterate_input(args):
    separator = args.separator + "\n" if args.separator else ""
    for root, dirs, files in os.walk(args.input):
        for f_path in files:
            with open(os.path.join(root, f_path)) as fp:
                if (args.exclude is not None and fnmatch.fnmatch(
                        fp.name, args.exclude)) or (args.include
                        is not None and not fnmatch.fnmatch(fp.name,
                        args.include)):
                    continue
                s = fill_template(fp.read(), **args.template_keys)
                if args.output_dir is not None:
                    if os.path.isfile(args.output_dir):
                        raise ConfigException(
                            "{} already exists and is a file".format(
                            args.output_dir))
                    elif not os.path.isdir(args.output_dir):
                        os.mkdir(args.output_dir)
                    with open(os.path.join(args.output_dir, f_path),
                            "w") as output_fp:
                        output_fp.write(s)
                else:
                    if s[-1] != "\n":
                        s += "\n"
                    sys.stdout.write(s + separator)

def main():
    args = setup_args()
    if args.template_keys_file is not None:
        args.template_keys = merge_template_keys(args.template_keys_file,
            args.template_keys)
    try:
        if os.path.isfile(args.input):
            with open(args.input) as input_fp:
                s = fill_template(input_fp.read(), **args.template_keys)
                sys.stdout.write(s)
        elif os.path.isdir(args.input):
            iterate_input(args)
        else:
            raise ConfigException("invalid file {}".format(args.input))
    except ConfigException as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
