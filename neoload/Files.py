
from neoload import *

import tempfile
import shutil
import os
import logging
import sys
import yaml
from distutils.dir_util import copy_tree
from jsonschema.exceptions import ValidationError
import itertools
import requests
import zipfile

from .YamlParsing import *

SPECIAL_NLW_EXTENSION = "nlp"

def packageFiles(fileSpecs,validateOnly):
    logger = logging.getLogger("root")
    logger.debug(fileSpecs)
    pack = {}
    pack["success"] = False
    pack["message"] = ""

    try:
        # collect all files into a temporary location, zip and upload or run from there
        files = []
        for path in fileSpecs:
            parts = path.replace(";",":").split(":")
            files.extend(parts)

        tmpdir = tempfile.mkdtemp()

        #click.echo("tmpdir:"+tmpdir)
        default_yaml = None
        #print("Logging[Files] is set to: " + str(logger.getEffectiveLevel()))

        asCodeFiles = []

        #TODO: need to abstract out file-based acquisition, fall-back to public URL
        yamlSchema = None

        if False: # when locally building, this was nice, but packaged it missed below live pull in testing
            if os.path.exists(getJSONSchemaFilepath()):
                with open(getJSONSchemaFilepath()) as file:
                    yamlSchema = objectifyJSONSchema(file.read())

        if yamlSchema is None:
            try:
                yamlRaw = getLatestJSONSchema()
                if yamlRaw is not None:
                    yamlSchema = objectifyJSONSchema(yamlRaw)
            except:
                logger.error("Error while obtaining JSON Schema online: " + str(sys.exc_info()[1]))

        if yamlSchema is None:
            logger.warning("JSON Schema to validate YAML could not be obtained, but allowing for YAML to bypass validation.\nUnderlying error: " + str(sys.exc_info()[1]))

        hasYamlToValidateAgainst = (yamlSchema is not None)

        logger.info("hasYamlToValidateAgainst: " + str(hasYamlToValidateAgainst))

        all_files = []

        overridingZipFile = None

        if any(list(filter(lambda x: x.endswith(".zip"), files))):
            if len(files) > 1:
                raise Exception("If specifying a zip file, you can only specify that as the one file.")
            else:
                overridingZipFile = files[0]

        pack["removeAfter"] = True

        logger.info("overridingZipFile: " + str(overridingZipFile))
        pack["asCodeFiles"] = []
        pack["anyIsNLP"] = False

        if overridingZipFile is not None:
            try:
                zip = zipfile.ZipFile(overridingZipFile)
                namelist = zip.namelist()
                defaultyamls = list(filter(lambda x: x.lower() == "default.yaml",namelist))
                if any(defaultyamls):
                    pack["asCodeFiles"] = defaultyamls
            except Exception as err:
                logger.warning("Error while scouring zip file for YAMLs.", sys.exc_info()[0])

            pack["removeAfter"] = False
            pack["zipfile"] = overridingZipFile
            pack["success"] = True
        else:
            for path in files:
                logger.debug("Adding file spec: " + path)
                dir = None
                if os.path.isdir(path):
                    dir = os.path.realpath(path)
                elif os.path.isfile(path):
                    relativeTo = os.path.dirname(os.path.realpath(path))
                    validated = False

                    if isAsCodeFile(path):

                        validated = validateFile(path,yamlSchema, not hasYamlToValidateAgainst) # when this doesn't throw an error

                        if default_yaml is None: default_yaml = path
                        relativePath = getRelativePath(path,relativeTo) # relative to itself
                        asCodeFiles.append(relativePath)
                        logger.debug("Adding as-code file: " + relativePath)

                    # WAS: copy the whole directory
                    #dir = os.path.dirname(os.path.realpath(path))
                    all_files.append({
                        "path": path,
                        "relativeTo": relativeTo,
                        "validated": validated,
                    })
                    all_files.extend(
                        list(map(lambda p: {
                            "path": p,
                            "relativeTo": relativeTo,
                            "validated": False,
                        }, getSubfiles(path,relativeTo)))
                    )

                else:
                    raise Exception("File '" + path + "' could not be found.")

            anyIsNLP = False

            for relative in all_files:
                path = relative["path"]
                relativeTo = relative["relativeTo"]
                validated = relative["validated"]

                if not validated:
                    validated = validateFile(path,yamlSchema,not hasYamlToValidateAgainst)

                isNLP = path.lower().endswith(("."+SPECIAL_NLW_EXTENSION).lower())
                anyIsNLP = anyIsNLP or isNLP

                if validated:
                    relativePath = getRelativePath(path,relativeTo)
                    tmppath = joinPath([tmpdir,relativePath])
                    logger.debug("Would: '" + path + "' -> '" + tmppath + "'")

                    # copy just this file using same relative subpath structure as source
                    tmpsubdir = slicePath(tmppath,slice(0,-1))
                    tmpsubdirparts = tmpsubdir.split(os.path.sep)
                    for i in range(len(tmpsubdirparts)):
                        tmppartsuntil = tmpsubdirparts[slice(0,i+1)]
                        partpath = joinPath(tmppartsuntil)
                        if len(partpath.strip()) > 0 and not os.path.exists(partpath):
                            os.makedirs(partpath, exist_ok=True)
                    shutil.copy(path,tmppath)

                if isNLP:
                    parentDirPath = os.path.dirname(os.path.abspath(path))
                    contents = next(os.walk(parentDirPath))
                    subdirs = contents[1]
                    filenames = contents[2]
                    notexcludedfils = list(filter(lambda x: not path.lower().endswith(x.lower()) and not any(filter(lambda y: x.lower().endswith("."+y),["bak","old","ds_store"])), filenames))
                    notexcludedsubs = list(filter(lambda x: not x.lower() in ['results'] and not x.lower().startswith('recorded-'), subdirs))
                    parentRelPath = joinPath(tmppath.split(os.path.sep)[0:-1])
                    for fil in notexcludedfils:
                        subfilpath = parentDirPath + os.path.sep + fil
                        destpath = parentRelPath + os.path.sep + fil
                        shutil.copy(subfilpath,destpath)

                    for subdirname in notexcludedsubs:
                        subdirpath = parentDirPath + os.path.sep + subdirname
                        destpath = parentRelPath + os.path.sep + subdirname
                        shutil.copytree(subdirpath, destpath)

            ##if not validateOnly or anyIsNLP: # 20200301PSB since we're using --validate for NLPs, always produce zip
            logger.info("Zipping project files.") #TODO: only when larger than Xmb
            fd, tmpzip = tempfile.mkstemp(prefix='neoload-cli_')
            shutil.make_archive(tmpzip, 'zip', tmpdir) # creates new .zip file
            try:
                os.remove(tmpzip) # get rid of temp file without extension
            except Exception as err:
                logger.warning("Could not remove temp file in 'packageFiles':", sys.exc_info()[0])

            tmpzip = tmpzip+".zip"
            os.close(fd)

            shutil.rmtree(tmpdir)

            pack["zipfile"] = os.path.realpath(tmpzip)
            pack["asCodeFiles"] = asCodeFiles

            logger.info("Zip file created: " + pack["zipfile"])
            logger.info("As-code files: " + ",".join(asCodeFiles))

            pack["anyIsNLP"] = anyIsNLP
            pack["success"] = True

    except:
        pack["message"] = str(sys.exc_info()[1])

    return pack

def slicePath(path,slice):
    split = os.path.sep
    return split.join(path.split(split)[slice])
def joinPath(parts):
    return os.path.sep.join(parts)

def getRelativePath(path,relativeTo):
    logger = logging.getLogger("root")
    logger.debug("getRelativePath[path]: " + path)
    logger.debug("getRelativePath[relativeTo]: " + relativeTo)
    relativePath = os.path.realpath(path)#.replace(os.path.dirname(os.path.realpath(path)),"",1)
    relativePath = relativePath.replace(relativeTo,"")
    if relativePath.startswith("/"): relativePath = relativePath.replace("/","",1)
    if relativePath.startswith("\\"): relativePath = relativePath.replace("\\","",1)
    logger.debug("getRelativePath[relativePath]: " + relativePath)
    return relativePath

def getFolderSize(folder):
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

def validateFile(path,yamlSchema,passIfCantValidate):
    ret = False

    if isAsCodeFile(path):

        if yamlSchema is None and passIfCantValidate:
            ret = True
        else:
            basicValidation = validateBasicYAML(path)
            if not basicValidation["success"]:
                raise Exception("File '" + path + "' is not valid YAML: " + basicValidation["error"])

            ascodeValidation = validateNeoLoadYAML(path, yamlSchema)
            if not ascodeValidation["success"]:
                raise Exception("File '" + path + "' is not valid NeoLoad schema:\n\n" +
                    ascodeValidation["error"] + "\n\n" +
                    "Please visit https://github.com/Neotys-Labs/neoload-models/blob/v3/neoload-project/doc/v3/project.md for specification." +
                    "\n")

            ret = True # in above situations, Exception should be raised if ever False; bool return for pragmatism sake

    else:
        ret = True # consider all other files valid (csv, ...) without additional probing

    return ret

def validateBasicYAML(filepath):
    logger = logging.getLogger("root")
    result = {}
    result["success"] = False
    result["error"] = "Unknown parsing error."
    try:
        with open(filepath) as file:
            spec = yaml.load(file, Loader=yaml.FullLoader)
            result["success"] = True
    except:
        result["error"] = str(sys.exc_info()[1])

    return result

def validateNeoLoadYAML(filepath, schema):
    logger = logging.getLogger("root")
    result = {}
    result["success"] = False
    result["error"] = "Unknown parsing error."
    fileAccess = False
    spec = None
    try:
        with open(filepath) as file:
            fileAccess = True
            spec = yaml.load(file, Loader=yaml.FullLoader)
            if spec is None: spec = {}
        validateYaml(spec, schema)
        result["success"] = True
    except ValidationError as ex:
        msg = ex.message
        if 'does not match' in ex.message:
            parts = ex.message.split("does not match")
            part = parts[0].strip()
            if part.startswith("'") and part.endswith("'"):
                part = part[1:-1]
            with open(filepath) as file:
                for num, line in enumerate(file, 1):
                    if part in line:
                        msg += '\n\nfound at line:' + str(num)
        result["error"] = msg
    except:
        msg = str(sys.exc_info()[1])
        if not fileAccess:
            msg = "YAML file could not be accessed."
        elif spec is None:
            msg = "File contents were not valid YAML."
        result["error"] = msg

    return result

def getSubfiles(filepath,relativeTo):
    logger = logging.getLogger("root")
    found = []
    logger.debug("rel: " + getRelativePath(filepath,relativeTo))
    relDir = relativeTo
    logger.debug("relDir: " + relDir)

    if isAsCodeFile(filepath):
        with open(filepath) as file:
            spec = yaml.load(file, Loader=yaml.FullLoader)
            if spec is not None:
                #logger.debug("getSubfiles: " + str(spec))
                if "includes" in spec:
                    newpaths = list(map(lambda p: joinPath(
                        list(filter(lambda a: len(a) > 0,[relDir,p]))
                    ),spec["includes"]))
                    logger.debug("getSubfiles: " + str(newpaths))
                    found.extend(newpaths)
                if "variables" in spec:
                    variables = spec["variables"]
                    logger.debug("getSubfiles: found variables: " + str(variables))
                    for item in variables:
                        logger.debug("getSubfiles: found variable: " + str(item))
                        if "file" in item:
                            value = item["file"]
                            logger.debug("getSubfiles: found file variable: " + str(value))
                            found.append(joinPath([relDir,value["path"]]))

    return found

def isAsCodeFile(filepath):
    asCodeExtensions = ["yaml","yml","json"]
    return any(list(filter(lambda x: filepath.endswith("."+x), asCodeExtensions)))

def getLatestJSONSchema():
    if isOfflineMode():
        return None

    logger = logging.getLogger("root")

    logger.debug("Getting latest schema from Github")
    # this is a temporary hold-over until a more permanent 302 mechanism is created
    schemaUrl = "https://raw.githubusercontent.com/Neotys-Labs/neoload-cli/master/resources/as-code.latest.schema.json"
    response = requests.get(schemaUrl)
    return response.text
