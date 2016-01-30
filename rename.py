#!/usr/bin/env python2.7

import sys
import os
from os.path import isfile, join, isdir, getsize
import argparse
import csv
from prettytable import PrettyTable
import logging
from enum import Enum

#*********************************************
# Ideas:
#   * Add possible options for renaming (mainly can delete)
#   * rename.log to see which files were renamed
#   * rename.err to see which files had issues
#*********************************************
locations = []
FORMAT = '%(module)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=20)
logger = logging.getLogger('find_dup')

class OutputWriter(object):
    def write(self, *row):
        pass

    def flush(self):
        pass

class TableOutputWriter(OutputWriter):
    def __init__(self, columns, align=None):
        align = align or {}

        self.table = PrettyTable(columns)
        self.table.align = align.get('*', 'l')

        for column, alignment in align.items():
            self.table.align[column] = alignment

    def write(self, *row):
        self.table.add_row(row)

    def flush(self):
        print(self.table)

class CsvOutputWriter(OutputWriter):
    def __init__(self, columns, fileName):
        self.file = open(fileName, 'w')
        self.writer = csv.writer(self.file, delimiter=',')
        self.writer.writerow(columns)

    def write(self, *row):
        self.writer.writerow(row)

    def flush(self):
        print(self.file.name + ' written.')
        self.file.close()

def get_file_ext(file):
    return file.split('.')[-1].lower()

def is_custom_ext(file):
    return get_file_ext(file) == only_ext    

def is_excluded(file):
    return get_file_ext(file) not in excluded_exts

def generate_file(files, writer):
    for file in files:
        logger.info("File added: %s", file)
        writer.write(file,file)

def get_file_list(location, filters):
    return [ join(location,f) for f in os.listdir(location) if all(fil(join(location,f)) for fil in filters) ]

def find_locations(start_location, levels):
    if levels == 1:
        locations.append(start_location)
    else:
        locations.append(start_location)
        all_folders = [ join(start_location, d) for d in os.listdir(start_location) if isdir(join(start_location, d)) ]
        for folder in all_folders:
            find_locations(folder, levels-1)

def rename(read_file, action='dry_run'):
    logger.info ('read file: %s' % args.read_file)
    if action == 'dry_run':
        logger.warn('This is a dry run!')

    read_header = False
    readFile=csv.reader(open(args.read_file,'rU'), delimiter=',')
    
    #print read_file

    for line in readFile:
        original_file=line[0]
        new_file=line[1]

        if not read_header:
            read_header = True
            continue
        if read_file in original_file:
            continue

        if new_file == 'D' or new_file == 'd' or new_file == 'delete':
            new_file = 'Deleted'

        logger_msg="\n\tOriginal File: \t%s\n\tNew File: \t%s" %(original_file, new_file)
        logger.info(logger_msg)

        if action != 'dry_run':
            if new_file == 'Deleted':
                os.remove(original_file)
            else:
                os.rename(original_file, new_file)

def error(msg):
    logger.error(msg)
    sys.exit()

if __name__== '__main__':

    parser = argparse.ArgumentParser('Find Duplicates')
    parser.add_argument('--location',
                        help=('Where do you want to start the search '
                              '(default: "%(default)s")'),
                        default=os.getcwd())
    parser.add_argument('--only-extension',
                        help=('compare files with given extension'))
    parser.add_argument('--exclude-extensions',
                        help=('Which extensions should be ignored '
                              'Separate multiple extensions with space'),
                        nargs='+')
    parser.add_argument('--action',
                        help=('Action to take when executing the script. '
                            'generate: generate the file you need to edit for renaming '
                            'rename: read the generated file and rename based on the edit '
                            'dry_run: output what the rename process will do'),
                        default="dry_run",
                        choices=['generate', 'rename', 'dry_run'])
    parser.add_argument('--delete-empty-folders',
                        help=('Delete any empty folders '
                              '(default: "%(default)s")'),
                        default=False,
                        action='store_true',
                        dest='delete_empty_folders')
    parser.add_argument('--levels',
                        help=('How many nested levels to itterate from root folder. '
                              '(default: "%(default)s")'),
                        default=1,
                        type=int)
    parser.add_argument('--custom-locations',
                        help=('Run scripts on custom location '
                              'Separate multiple locations with space'),
                        nargs='+')
    parser.add_argument('--file-name', 
                        help=('Whad do you want to name the output file. '
                              '(default: %(default)s))'),
                        default='rename.csv')
    parser.add_argument('--read-file',
                        help=('Read file with modified locations. '
                              '(must be a csv file created by this program. default: %(default)s))'))

    args = parser.parse_args()

    filters = [isfile]
    columns = ['Original Name', 'Rename To']

    if args.action == 'dry_run':
        writer = TableOutputWriter(columns)  
    elif args.action == 'generate':
        writer = CsvOutputWriter(columns, args.file_name)


    if args.exclude_extensions:
        excluded_exts=args.exclude_extensions
        filters.append(is_excluded)

    if args.only_extension:
        only_ext=args.only_extension
        filters.append(is_custom_ext)

    if args.custom_locations:
        locations = args.custom_locations
    else:
        find_locations(args.location, args.levels)

    logger.info("Start!")
    
   
    if args.action == 'generate':
        logger.info("Generating %s", args.file_name)
        file_list = []
        for location in locations:
            logger.info("Adding files from '%s' to list", location)
            file_list = file_list + get_file_list(location, filters)
        generate_file(file_list, writer)
        writer.flush()
    elif args.action == 'dry_run' or args.action == 'rename':
        if not args.read_file:
            error("--read-file option not set!")
        else:
            rename(args.read_file, args.action)
    else:
        logger.info("Action '%s' not found!", args.action)

    logger.info("Done!")