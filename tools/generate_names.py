##########################################################################
#
# Script for automatically generating the Python module: simfin/names.py
#
# Instructions:
#
# 1) Run this command in a terminal: python generate_names.py
#    This downloads the definitions from the SimFin-server and
#    creates the file 'names.py' in the current directory.
# 2) Compare the new and old files using diff and make sure it looks OK.
# 3) Move 'names.py' to the appropriate simfin-directory.
# 4) Run the automated testing for the Notebook tutorials to ensure
#    they still work with the new 'names.py'
#
##########################################################################
# SimFin - Simple financial data for Python.
# www.simfin.com - www.github.com/simfin/simfin
# See README.md for instructions and LICENSE.txt for license details.
##########################################################################

import numpy as np
import requests
import sys

from textwrap import TextWrapper

from simfin.download import _url_info

##########################################################################

# Name of the output-file.
_output_filename = 'names.py'

# Header that will be written in names.py
_header = \
"""##########################################################################
#
# Names that makes it easier to address individual data-columns.
# For example, you can write df[SGA] instead of
# df['Selling, General & Administrative'] to get the same data.
#
# For a better overview of the datasets and their data-columns, see:
# https://simfin.com/data/access/bulk
#
# This file was auto-generated by the script: tools/generate_names.py
#
##########################################################################
# SimFin - Simple financial data for Python.
# www.simfin.com - www.github.com/simfin/simfin
# See README.md for instructions and LICENSE.txt for license details.
##########################################################################

# Import all the extra names that have been manually defined. This makes
# them available for import through this auto-generated module as well.
from simfin.names_extra import *

##########################################################################
"""

# Section-separator that will be written in names.py
_separator = '##########################################################################'

##########################################################################
# Helper-functions.

def _get_duplicates(x):
    """Return a list with the elements from x that are duplicates."""

    # Ensure x is a numpy array.
    x = np.array(x)

    # Index of unique elements in x.
    _, idx = np.unique(x, return_index=True)

    # Create boolean mask of elements in x that are duplicates.
    duplicate_mask = np.ones(len(x), dtype=np.bool)
    duplicate_mask[idx] = False

    # Return the elements in x that are duplicates.
    return list(x[duplicate_mask])


def _print_duplicates(x):
    """Print the duplicates from x to stderr."""

    # Get the list of duplicates.
    duplicates = _get_duplicates(x)

    # If there are any duplicates.
    if len(duplicates)>0:
        # Print error-header.
        msg = 'Duplicates: {}'.format(len(duplicates))
        print(msg, file=sys.stderr)

        # Print all the duplicates.
        for dup in duplicates:
            print('- ' + dup, file=sys.stderr)

        # Print newline.
        print('', file=sys.stderr)

##########################################################################
# Main processing function.

def _process():
    """
    Download json-file from the SimFin-server with all the definitions of
    names, shortcuts and descriptions. Handle duplicates and write the
    output to the file names.py
    """

    # URL for the json-file that will be converted into names.py
    url = _url_info(name='columns')

    # Download the json-file from the web-server.
    # We do not use the function load_info_columns() because it would
    # save the json-file to disk and require us to set a data-dir.
    response = requests.get(url=url)
    data = response.json()

    # Data-structure for the organized data after handling duplicate names etc.
    data_organized = {}

    # List of all the column-names e.g. ['Revenue', 'Net Income', ...]
    # This is used to find and report duplicates.
    all_names = []

    # List of all the shortcuts e.g. ['REVENUE', 'NET_INCOME', ...]
    # This is used to find and report duplicates.
    all_shortcuts = []

    # Process the json data.
    for record in data:
        # Name of the data-column e.g. 'Cash & Equivalents'
        name = record['name']

        # Append to list of all names.
        all_names.append(name)

        # Shortcuts of the data-column. This is a list with one or more strings.
        # For example: ['CASH_EQUIVALENTS'] or ['SHARE_PRICE', 'CLOSE'].
        shortcuts = record['shortcuts']

        # Append to list of all shortcuts.
        all_shortcuts += shortcuts

        # Description of the data.
        description = record.get('description', "")

        # Lookup the record for this name in the organized data-structure.
        record_org = data_organized.get(name)

        # If the record does not exist, initialize an empty record.
        if record_org is None:
            record_org = \
                {
                    'shortcuts': [],
                    'descriptions': []
                }

        # Append the list of shortcuts for this name.
        record_org['shortcuts'] += shortcuts

        # Append the description if it is non-empty.
        if description != "":
            record_org['descriptions'] += [description]

        # Update the record in the organized data-structure.
        data_organized[name] = record_org

    # At this point the entire json-file has been organized and we now
    # want to write the data to the names.py file.

    # Text-wrapper to ensure comment-lines are kept within the given length.
    wrapper = TextWrapper(width=80,
                          initial_indent='# ',
                          subsequent_indent='# ')

    # Create the output file.
    with open(_output_filename, mode='wt') as file:
        # Write header to the file.
        print(_header, file=file)

        # Write all the descriptions, shortcuts and names to file.
        # This will be sorted ascendingly by name.
        for name, record_org in sorted(data_organized.items()):
            # Get the list of shortcuts for this name.
            shortcuts = record_org['shortcuts']

            # Get the list of descriptions for this name.
            descriptions = record_org['descriptions']

            # Write the descriptions to file.
            if len(descriptions) > 0:
                if len(descriptions) == 1:
                    # If there is only one description, write it without numbering.
                    description = descriptions[0]
                else:
                    # If there is more than one description for this name, which
                    # can occur when there are multiple definitions for a name,
                    # then write it with numbering to separate the descriptions.
                    description = ""
                    for i, descr in enumerate(descriptions):
                        description += "({}) ".format(i+1) + descr.strip() + " "

                # Break the description into lines of some max-length.
                # This should split and wrap the words correctly.
                desc_lines = wrapper.wrap(description.strip())

                # Write the description lines to file.
                for line in desc_lines:
                    print(line, file=file)

            # Ensure the shortcuts are unique for this name.
            shortcuts = list(set(shortcuts))

            # Write shortcut(s) to file e.g. 'CLOSE = SHARE_PRICE = '
            # This will be sorted ascendingly.
            for shortcut in sorted(shortcuts):
                print(shortcut + ' = ', sep='', end='', file=file)

            # Write name to file e.g. 'Close'
            print('\'' + name + '\'', sep='', file=file)

            # Write newline to file.
            print(file=file)

        # Write section-separator to file.
        print(_separator, file=file)

    # Print all duplicate names.
    _print_duplicates(all_names)

    # Print all duplicate shortcuts.
    _print_duplicates(all_shortcuts)

##########################################################################

if __name__ == "__main__":
    _process()

##########################################################################
