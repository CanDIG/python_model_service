"""
Pre- and post- hooks for the dredd tests to ensure that
the tests are made in the correct order, and that IDs
returned previously are used in proceeding API calls
"""
import json
import dredd_hooks as hooks

ORDER = ["/v1/individuals > Add an individual to the database > 201 > application/json",
         "/v1/individuals > Add an individual to the database > 405 > application/json",
         "/v1/individuals > Get all individuals > 200 > application/json",
         "/v1/individuals/{individual_id} > Get specific individual > 404 > application/json",
         "/v1/individuals/{individual_id} > Get specific individual > 200 > application/json",
         "/v1/individuals/{individual_id} > Update specific individual > 204 > application/json",
         "/v1/individuals/{individual_id} > Update specific individual > 404 > application/json",
         "/v1/variants > Add a variant to the database > 201 > application/json",
         "/v1/variants > Add a variant to the database > 405 > application/json",
         "/v1/variants > Get all variants within genomic range > 200 > application/json",
         "/v1/variants/{variant_id} > Get specific variant > 200 > application/json",
         "/v1/variants/{variant_id} > Get specific variant > 404 > application/json",
         "/v1/variants/{variant_id} > Update specific variant > 204 > application/json",
         "/v1/variants/{variant_id} > Update specific variant > 404 > application/json",
         "/v1/calls > Add a call to the database > 201 > application/json",
         "/v1/calls > Add a call to the database > 405 > application/json",
         "/v1/calls > Get all calls > 200 > application/json",
         "/v1/calls/{call_id} > Get specific call > 200 > application/json",
         "/v1/calls/{call_id} > Get specific call > 404 > application/json",
         "/v1/calls/{call_id} > Update specific call > 204 > application/json",
         "/v1/calls/{call_id} > Update specific call > 404 > application/json",
         "/v1/individuals/{individual_id}/variants > Get variants called in an individual > 200 > application/json",
         "/v1/individuals/{individual_id}/variants > Get variants called in an individual > 404 > application/json",
         "/v1/variants/{variant_id}/individuals > Get individuals with a given variant called > 200 > application/json",
         "/v1/variants/{variant_id}/individuals > Get individuals with a given variant called > 404 > application/json",
         "/v1/individuals/{individual_id} > Delete specific individual > 204 > application/json",
         "/v1/individuals/{individual_id} > Delete specific individual > 404 > application/json",
         "/v1/variants/{variant_id} > Delete specific variant > 204 > application/json",
         "/v1/variants/{variant_id} > Delete specific variant > 404 > application/json",
         "/v1/calls/{call} > Delete specific call > 404 > application/json"]

@hooks.before_all
def reorder_actions(transactions):
    """
    Order the endpoint calls in the order given by ORDER,
    skipping calls that aren't present.

    Optionally output all the endpoints in an easy-to-use format
    """
    OUTPUT_ENDPOINTS = False
    def sort_key(transaction):
        if not transaction['name'] in ORDER:
            return 10000
        else:
            return ORDER.index(transaction['name'])

    transactions.sort(key=sort_key)
    for transaction in transactions:
        transaction['skip'] = (transaction['name'] not in ORDER)

    if OUTPUT_ENDPOINTS:
        with open('endpoints.txt', 'w') as outfile:
            for transaction in transactions:
                print('"'+transaction['name']+'",', file=outfile)


UUID_EXAMPLE = "bf3ba75b-8dfe-4619-b832-31c4a087a589"
RO_FIELDS = ["created", "updated", "id"]
response_stash = {}

@hooks.before_each
def redact_readonly_fields(transaction):
    """Do not send readonly (computed) fields"""
    # no action necessary if not a POST or PUT
    if transaction['request']['method'] in ["POST", "PUT"]:
        # otherwise, remove such fields from the request body
        request_body = json.loads(transaction['request']['body'])
        for ro_field in RO_FIELDS:
            if ro_field in request_body:
                del request_body[ro_field]
        transaction['request']['body'] = json.dumps(request_body)


@hooks.after("/v1/individuals > Get all individuals > 200 > application/json")
def save_individuals_response(transaction):
    """
    Save the individual ids returned from the get all call
    """
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['individual_ids'] = ids


@hooks.after("/v1/variants > Get all variants within genomic range > 200 > application/json")
def save_variants_response(transaction):
    """
    Save the variant ids returned from the get all call
    """
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['variant_ids'] = ids


@hooks.after("/v1/calls > Get all calls > 200 > application/json")
def save_calls_response(transaction):
    """
    Save the call ids returned from the get all call
    """
    parsed_body = json.loads(transaction['real']['body'])
    ids = [item['id'] for item in parsed_body]
    response_stash['call_ids'] = ids


@hooks.before("/v1/individuals/{individual_id} > Update specific individual > 204 > application/json")
@hooks.before("/v1/individuals/{individual_id}/variants > Get variants called in an individual > 200 > application/json")
@hooks.before("/v1/individuals/{individual_id} > Get specific individual > 200 > application/json")
@hooks.before("/v1/individuals/{individual_id} > Delete specific individual > 204 > application/json")
@hooks.before("/v1/individuals/{individual_id} > Delete specific individual > 404 > application/json")
def insert_individual_id(transaction):
    "Put the saved individual ID into the URL"
    transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['individual_ids'][0])


@hooks.before("/v1/variants/{variant_id}/individuals > Get individuals with a given variant called > 200 > application/json")
@hooks.before("/v1/variants/{variant_id} > Get specific variant > 200 > application/json")
@hooks.before("/v1/variants/{variant_id} > Update specific variant > 204 > application/json")
@hooks.before("/v1/variants/{variant_id} > Delete specific variant > 204 > application/json")
@hooks.before("/v1/variants/{variant_id} > Delete specific variant > 404 > application/json")
def insert_variant_id(transaction):
    "Put the saved variant ID into the URL"
    if 'variant_ids' in response_stash:
        transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['variant_ids'][0])


@hooks.before("/v1/calls/{call_id} > Get specific call > 200 > application/json")
@hooks.before("/v1/calls/{call_id} > Update specific call > 204 > application/json")
@hooks.before("/v1/calls/{call_id} > Delete specific call > 404 > application/json")
def insert_call_id(transaction):
    "Put the saved call ID into the URL"
    transaction['fullPath'] = transaction['fullPath'].replace(UUID_EXAMPLE, response_stash['call_ids'][0])


@hooks.before("/v1/calls > Add a call to the database > 201 > application/json")
@hooks.before("/v1/calls > Add a call to the database > 405 > application/json")
def prepare_call_request(transaction):
    """Update the body of the example call with saved variant and individual ids"""
    request_body = json.loads(transaction['request']['body'])
    request_body['individual_id'] = response_stash['individual_ids'][0]
    request_body['variant_id'] = response_stash['variant_ids'][0]
    transaction['request']['body'] = json.dumps(request_body)
