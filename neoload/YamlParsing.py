from jsonschema import validate
import logging
import yaml
import json
import itertools
import os

def getJSONSchemaFilepath():
    logger = logging.getLogger("root")
    schemaParts = os.path.abspath(__file__).split(os.path.sep)
    schemaParts = list(itertools.islice(schemaParts,len(schemaParts)-2))
    schemaParts.extend([
        "resources",
        "as-code.latest.schema.json"
    ])
    schemaFilepath = os.path.sep.join(schemaParts)
    logging.debug("schemaFilepath: " + schemaFilepath)
    return schemaFilepath

def objectifyJSONSchema(text): # raises exceptions
    return json.loads(text)

def validateYaml(yamlObjectified, schemaObjectified): # raises exceptions
    validate(yamlObjectified, schemaObjectified) # passes
