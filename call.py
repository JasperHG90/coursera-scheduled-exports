#! /usr/bin/env python

'''
Copyright 2016 Leiden University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

'''
# Call this script using crontab to download & store coursera export data at scheduled times.
# Jasper Ginn
# 07/10/2016
'''

import os
import argparse
import logging
import datetime
from urlparse import urlparse
from scheduler import coursera

'''
Wrapper to download files.
'''

def coursera_download(course_slug, request_type, location, store_metadata = True):

    if not os.path.exists("{}{}".format(location, request_type)):
        os.makedirs("{}{}".format(location, request_type))
    # Check if course slug folder exists in data folder
    if not os.path.exists("{}{}/{}".format(location, request_type, course_slug)):
        os.makedirs("{}{}/{}".format(location, request_type, course_slug))
    # Init
    c = coursera(course_slug, args.verbose)
    # Fetch course id
    c.get_course_id()
    if args.verbose:
        print 'Sucessfully fetched course ID'
    # Depending on request type, call tables or clickstream
    if request_type == 'clickstream':
        c.request_clickstream()
    else:
        c.request_schemas()
    if args.verbose:
        print 'Successful request'
    # Check if ready for download
    links = c.status_export(interval = 300)
    # Download data to destination folder
    for link in links:
        # Check if file exists
        filename = urlparse(link).path.split('/')[-1]
        # Create location
        tloc = "{}{}/{}/".format(location, request_type, course_slug)
        if os.path.isfile("{}{}".format(tloc, filename)):
            logging.info("File {} already exists in target location. Moving on ... ".format(filename))
            continue
        c.download(link, tloc)
    # Get metadata and store in file
    if store_metadata:
        meta = c.return_metadata()
        time_now = datetime.datetime.now()
        with open("{}/metadata.txt".format(location), 'a') as inFile:
            inFile.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(time_now.encode("utf8"), meta["course"].encode("utf8"),
                                                         meta["course_id"].encode("utf8"), meta["exportType"].encode("utf8"),
                                                         meta["meta"].encode("utf8"), meta["schemaNames"].encode("utf8")))

'''
Run file
'''

if __name__=="__main__":

    # Set up parser and add arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("export_type", help="Either one of 'clickstream' or 'tables'", type=str, choices=["clickstream", "tables"])
    parser.add_argument("course_slugs", help="EITHER: A course slug name or names separated by a comma, OR: Location of a text file (.txt) containing multiple course slug names. Each slug should be placed on a new line.", type=str)
    parser.add_argument("location", help="Base directory in which to store the data. The program will automatically add the course slug to the folder and download the data there.", type = str)
    parser.add_argument("-m", "--save_metadata", help="Add the course's metadata to a 'metadata.txt' file saved in the base directory? Defaults to 'True'. If file does not exist, it will be created.", action="store_true")
    parser.add_argument("-v", "--verbose", help="Print verbose messages.", action="store_true")
    args = parser.parse_args()

    # Check directories
    if args.location != None:
        if not os.path.exists(args.location):
            raise RuntimeError("Directory {} does not exist.".format(args.location))

    # Check slugs. If slug is mispelled it will be caught downstream in the coursera class.
    if ".txt" in args.course_slugs:
        with open(args.course_slugs, 'r') as inFile:
            courseSlugs = [line.replace("\n", "").replace(" ", "") for line in inFile]
    else:
        # Check if a filepath
        if os.path.isfile(args.course_slugs):
            raise RuntimeError("You entered a file path but the destination file is not a .txt file.")
        elif '/' in args.course_slugs:
            raise RuntimeError("You entered an invalid file path. Additionally, the file path you specified did not contain a .txt file.")
        elif '.' in args.course_slugs:
            raise RuntimeError("You entered a file type that is currently not supported. Type --help for more information.")
        else:
            courseSlugs = [cl.replace(" ", "") for cl in args.course_slugs.split(",")]

    # Check if location ends with '/'. If it does not, add.
    if not args.location.endswith("/"):
        args.location = "{}/".format(args.location)

    # Create logger here!
    logging.basicConfig(filename = "{}{}".format(args.location, "scheduled_downloads.log"), filemode='a', format='%(asctime)s %(name)s %(levelname)s %(message)s',
                        level=logging.INFO)

    # Call
    for courseSlug in courseSlugs:
        coursera_download(courseSlug, args.export_type, args.location, args.save_metadata)
