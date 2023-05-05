import argparse

from Code.create_yelp_nt_files import create_nt_file, create_checkin_nt_file, create_tip_nt_file
from Code.create_schema_nt_files import create_schema_hierarchy_file, create_schema_mappings_file
from Code.KnowledgeGraphEnrichment.create_schema_wiki_mapping import create_yelp_wiki_mapping
from Code.KnowledgeGraphEnrichment.location_from_wikidata import create_locations_nt

parser = argparse.ArgumentParser()

parser.add_argument('--read_dir', type=str, help='Your directory to read data from')
parser.add_argument('--write_dir', type=str, help='Your directory to write data to')
parser.add_argument('--include_schema', type=bool, help='Whether to include Schema links in the YKCG')
parser.add_argument('--include_wikidata', type=bool, help='Whether to include Wikidata links in the YKCG')

args = parser.parse_args()

read_dir = args.read_dir
write_dir = args.write_dir
include_schema = args.include_schema
include_wikidata = args.include_wikidata

files = [
        'yelp_academic_dataset_business.json',
        'yelp_academic_dataset_user.json',
        'yelp_academic_dataset_review.json'
    ]

for file in files:
    create_nt_file(file_name=file, read_dir=read_dir, write_dir=write_dir)
    print("Finished creating NT file for " + file)

create_checkin_nt_file(read_dir=read_dir, write_dir=write_dir)
print("Finished creating Checkin NT file")
create_tip_nt_file(read_dir=read_dir, write_dir=write_dir)
print("Finished creating all Yelp NT files")

# # Creates the Schema triple files
if include_schema:
    create_schema_hierarchy_file(read_dir=read_dir, write_dir=write_dir)
    print("Finished creating Schema Hierarchy NT file")
    create_schema_mappings_file(read_dir=read_dir, write_dir=write_dir)
    print("Finished creating Schema Mappings NT file")

# Creates the Wikidata triple files
if include_wikidata:
    create_yelp_wiki_mapping(read_dir=read_dir, write_dir=write_dir)
    print("Finished creating Wikidata Mapping NT file")
    create_locations_nt(read_dir=read_dir, write_dir=write_dir)
    print("Finished creating Wikidata location NT file")
