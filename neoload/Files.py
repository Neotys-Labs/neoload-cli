import tempfile
import shutil
import os
import logging
import sys
import yaml
from distutils.dir_util import copy_tree

def packageFiles(fileSpecs):
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

        file_list = files
        tmpdir = tempfile.mkdtemp()

        #click.echo("tmpdir:"+tmpdir)
        default_yaml = None
        #print("Logging[Files] is set to: " + str(logger.getEffectiveLevel()))
        logger.info("Zipping project files.") #TODO: only when larger than Xmb

        asCodeFiles = []

        for path in file_list:
            dir = None
            if os.path.isdir(path):
                dir = os.path.realpath(path)
            elif os.path.isfile(path):
                if path.endswith(".yaml"):
                    basicValidation = validateBasicYAML(path)
                    if not basicValidation["success"]:
                        raise Exception("File '" + path + "' is not valid YAML: " + basicValidation["error"])
                    if not validateNeoLoadYAML(path):
                        raise Exception("File '" + path + "' is not valid NeoLoad YAML.")
                    if default_yaml is None: default_yaml = path
                    relativePath = os.path.realpath(path).replace(os.path.dirname(os.path.realpath(path)),"",1)
                    if relativePath.startswith("/"): relativePath = relativePath.replace("/","",1)
                    if relativePath.startswith("\\"): relativePath = relativePath.replace("\\","",1)
                    asCodeFiles.append(relativePath)
                    logger.debug("Adding as-code file: " + relativePath)
                dir = os.path.dirname(os.path.realpath(path))
            else:
                raise Exception("File '" + path + "' could not be found.")

            if dir is not None:
                #click.echo(dir)
                copy_tree(dir,tmpdir)

        # if default_yaml is not None:
        #     names = os.listdir(tmpdir)
        #     for name in names:
        #         if name == os.path.basename(default_yaml):
        #             os.rename(tmpdir+"/"+name,tmpdir+"/default.yaml")


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

        pack["success"] = True

    except:
        pack["message"] = str(sys.exc_info()[1])

    return pack

def getFolderSize(folder):
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

def validateBasicYAML(filepath):
    logger = logging.getLogger("root")
    result = {}
    result["success"] = False
    result["error"] = "Unknown parsing error."
    try:
        with open(filepath) as file:
            spec = yaml.load(file, Loader=yaml.FullLoader)
    except:
        result["error"] = str(sys.exc_info()[1])

    return result

def validateNeoLoadYAML(filepath):
    return True
