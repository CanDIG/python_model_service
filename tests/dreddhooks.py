import json
import dredd_hooks as hooks

UUID_EXAMPLE="bf3ba75b-8dfe-4619-b832-31c4a087a589"
response_stash = {}

@hooks.after("/individuals > Get all individuals > 200 > application/json")
def save_individuals_response(transaction):
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['individual_ids'] = ids

@hooks.after("/variants > Get all variants within genomic range > 200 > application/json")
def save_variants_response(transaction):
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['variant_ids'] = ids

@hooks.before("/individuals/{individual_id}/variants > Get variants called in an individual > 200 > application/json")
def insert_individual_id(transaction):
    transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['individual_ids'][0])

@hooks.before("/variants/{variant_id}/individuals > Get individuals with a given variant called > 200 > application/json")
def insert_variant_id(transaction):
    transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['variant_ids'][0])
