#!/usr/bin/env python3
## @author Copyright (C) 2017-2018 Robin Schneider <robin.schneider@geberit.com>
## @company Copyright (C) 2017-2018 Geberit Verwaltungs GmbH https://www.geberit.de
## @license AGPL-3.0-only <https://www.gnu.org/licenses/agpl-3.0.html>
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, version 3 of the
## License.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <https://www.gnu.org/licenses/>.

__license__ = 'AGPL-3.0-only'
__author__ = 'Robin Schneider <robin.schneider@geberit.com>'
__version__ = '0.5.0'

# core modules {{{
import sys
import os
import logging
import json

from collections import defaultdict
# }}}


def find_and_update_issues(obj, issues, tag_field):
    tags_to_exclude = set([
        '_geoip_lookup_failure',
        '_host_location_parsefailure',
    ])

    if tag_field in obj:
        tags = obj[tag_field]
        if isinstance(tags, str):
            tags = [tags]

        logger.info(tags)

        for tag in tags:
            if tag.startswith('_') and tag not in tags_to_exclude:
                issues[tag] += 1


# main {{{
if __name__ == '__main__':
    from argparse import ArgumentParser

    # Script Arguments {{{
    args_parser = ArgumentParser(
        description=__doc__,
        # epilog=__doc__,
    )
    args_parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s {version}'.format(version=__version__)
    )
    args_parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements.",
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    args_parser.add_argument(
        '-v', '--verbose',
        help="Be verbose.",
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
    )
    args_parser.add_argument(
        '-t', '--tag-field',
        help="Field name where to look for Logstash tags.",
        default='tags',
    )
    args_parser.add_argument(
        '-l', '--log-to-files',
        help="Log issues to files with the same file namespace where they where found.",
        action='store_true',
    )
    args_parser.add_argument(
        'files',
        help="Input JSON files to check.",
        nargs='+',
    )
    args = args_parser.parse_args()
    logger = logging.getLogger(__file__)
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=args.loglevel,
    )

    exit_code = 0
    successful_json_loads = 0

    for file_name in args.files:
        file_ns = '.'.join(file_name.split('.')[:-1])
        if args.log_to_files:
            log_to_file_h = logging.FileHandler(file_ns + '.issues', mode='w')
            logger.addHandler(log_to_file_h)

        with open(file_name, 'r', encoding='utf-8') as fh:
            ## This only works for one JSON object per line. If your file looks
            ## different generate one with the right format.
            ## There is no standard on how to put multiple JSON objects into
            ## the same file. One could use a JSON array but this is not useful
            ## for this case Logstash.
            ## The command to get the right format is `jq '.' input.json --compact-output > output.json`

            issues = defaultdict(int)
            for json_line in fh:
                try:
                    data = json.loads(json_line)
                except ValueError:
                    logger.info('Cound not de-serialize line: {}'.format(
                        json_line.rstrip(),
                    ))
                else:
                    successful_json_loads += 1
                    find_and_update_issues(data, issues, args.tag_field)
                    logger.debug(data)

            if len(issues):
                exit_code += 1
                logger.warn('Found issues in file {}: {}'.format(
                    file_name,
                    ['{}={}'.format(k, issues[k]) for ind, k in enumerate(sorted(issues, key=lambda x: (issues[x], x)))],
                ))

        if args.log_to_files:
            logger.removeHandler(log_to_file_h)
            log_to_file_h.close()
            if os.path.getsize(file_ns + '.issues') == 0:
                os.remove(file_ns + '.issues')


    if exit_code > 100:
        exit_code = 101

    if successful_json_loads == 0 and len(args.files) != 0:
        logger.warn('No JSON documents could be deserialized but {} files containing JSON lines where given.'.format(
            len(args.files),
        ))
        exit_code += 1

    if exit_code >= 1:
        logger.warn('Issues occured, exiting with exit code {}'.format(
            exit_code,
        ))

    sys.exit(exit_code)

# }}}
