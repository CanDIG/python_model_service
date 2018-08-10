import json
import dredd_hooks as hooks

UUID_EXAMPLE = "bf3ba75b-8dfe-4619-b832-31c4a087a589"
response_stash = {}


@hooks.after("/v1/individuals > Get all individuals > 200 > application/json")
def save_individuals_response(transaction):
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['individual_ids'] = ids


@hooks.after("/v1/variants > Get all variants within genomic range > 200 > application/json")
def save_variants_response(transaction):
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['variant_ids'] = ids


@hooks.before("/v1/calls > Add a call to the database > 201 > application/json")
def print_transaction(transaction):
    request_body = json.loads(transaction['request']['body'])
    request_body['individual_id'] = response_stash['individual_ids'][0]
    request_body['variant_id'] = response_stash['variant_ids'][0]
    transaction['request']['body'] = json.dumps(request_body)


@hooks.after("/v1/calls > Get all calls > 200 > application/json")
def save_calls_response(transaction):
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['call_ids'] = ids


@hooks.before("/v1/individuals/{individual_id}/variants > Get variants called in an individual > 200 > application/json")
@hooks.before("/v1/individuals/{individual_id} > Get specific individual > 200 > application/json")
def insert_individual_id(transaction):
    transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['individual_ids'][0])


@hooks.before("/v1/variants/{variant_id}/individuals > Get individuals with a given variant called > 200 > application/json")
@hooks.before("/v1/variants/{variant_id} > Get specific variant > 200 > application/json")
def insert_variant_id(transaction):
    if 'variant_ids' in response_stash:
        transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['variant_ids'][0])


@hooks.before("/v1/calls/{call_id} > Get specific call > 200 > application/json")
def insert_vall_id(transaction):
    transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['call_ids'][0])


@hooks.before("/v1/individuals/{individual_id} > Get specific individual > 404 > application/json")
@hooks.before("/v1/variants/{variant_id} > Get specific variant > 404 > application/json")
@hooks.before("/v1/calls/{call_id} > Get specific call > 404 > application/json")
@hooks.before("/v1/individuals/{individual_id}/variants > Get variants called in an individual > 404 > application/json")
@hooks.before("/v1/variants/{variant_id}/individuals > Get individuals with a given variant called > 404 > application/json")
def let_pass(transaction):
    transaction['skip'] = False
