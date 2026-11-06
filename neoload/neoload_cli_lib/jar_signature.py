import logging
import os
import shutil
import subprocess
import zipfile
from itertools import groupby

from neoload_cli_lib import cli_exception, resources

CMS_SIGNATURE_ENTRY = "META-INF/NEOLOAD_.RSA"
SIGNATURE_BLOCK_SUFFIXES = (".RSA", ".DSA", ".EC")
EXPECTED_ORGANIZATION = "Tricentis GmbH"
CERTIFICATE_NAMESPACE = "resources.certs"
TRUSTED_ROOT_KEYSTORE = "globalsign-code-signing-root-r45.jks"
KEPT_ENTRY_LINES = 3

class JarSignatureError(cli_exception.CliException):
    pass


class JarVerificationUnavailableError(JarSignatureError):
    """No verdict could be reached on the JAR, the check itself could not run."""
    pass


def verify_signed_by_tricentis(jar_path, java_executable):
    """Raise JarSignatureError unless
     - jar signature is verified against trusted root
     - subject DN is Tricentis GmbH
     - that signature is the only one the jar carries
    """
    jarsigner = _locate_jarsigner(java_executable)
    try:
        _check_signature(jar_path, jarsigner)
    except JarSignatureError as err:
        if isinstance(err, JarVerificationUnavailableError):
            raise
        raise _rejected_as_unofficial(jar_path, err)


def _check_signature(jar_path, jarsigner):
    try:
        archive = zipfile.ZipFile(jar_path)
    except (OSError, zipfile.BadZipFile) as err:
        raise JarSignatureError("'{0}' is not a readable JAR: {1}".format(jar_path, err))

    with archive as jar:
        cms_signature = _read_cms_signature(jar)
        _check_tricentis_is_the_only_signer(jar)

    _run_jarsigner(jar_path, jarsigner)
    _check_signer_is_tricentis(cms_signature)


def _rejected_as_unofficial(jar_path, cause):
    """Wrap a failed check into the message the user acts on.

    The technical wording comes first and the verdict last, so that the line
    the user reads right above the prompt is the one that matters, as in a
    Python traceback.
    """
    details = "\n".join("  " + line for line in str(cause).splitlines())
    return JarSignatureError(
        "Signature check details:\n{0}\n\n"
        "CheckVU did not run, for security reasons: '{1}' is not an official CheckVU JAR. "
        "Either the file was modified after Tricentis released it, or it is not a CheckVU "
        "JAR at all.\n"
        "Download CheckVU again, or pass a JAR you trust with --jar."
        .format(details, jar_path))


def _read_cms_signature(jar):
    """Read the signature block jarsigner wrote at META-INF/NEOLOAD_.RSA."""
    try:
        return jar.read(CMS_SIGNATURE_ENTRY)
    except KeyError:
        raise JarSignatureError(
            "The CheckVU JAR is not signed: no signature block '{0}' found."
            .format(CMS_SIGNATURE_ENTRY))


def _check_tricentis_is_the_only_signer(jar):
    """Raise unless the Tricentis block is the only one.
    """
    blocks = [name for name in jar.namelist() if _is_signature_block(name)]
    if blocks != [CMS_SIGNATURE_ENTRY]:
        raise JarSignatureError(
            "The CheckVU JAR must carry the Tricentis signature and nothing else, but holds {0}."
            .format(", ".join(blocks)))


def _is_signature_block(entry_name):
    """Tell whether Java would read an entry as a signature block.
    Based on conditions in JVM itself
    """
    directory, _, filename = entry_name.rpartition("/")
    return (directory.upper() == "META-INF"
            and filename.upper().endswith(SIGNATURE_BLOCK_SUFFIXES))


def _run_jarsigner(jar_path, jarsigner):
    """Let the JDK verify the signature against the root shipped with this package.
    Verification is strict (validates whole cert chain, no unsigned entries, no
    modifications)"""
    with resources.get_resource_as_path(CERTIFICATE_NAMESPACE, TRUSTED_ROOT_KEYSTORE) as truststore:
        command = [jarsigner, "-verify", "-strict", "-keystore", str(truststore), jar_path]
        try:
            completed = subprocess.run(command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       universal_newlines=True,
                                       errors="replace")
        except OSError as err:
            raise JarVerificationUnavailableError(
                "Unable to run '{0}' to verify the CheckVU JAR: {1}".format(jarsigner, err))

    if completed.returncode != 0:
        output = (completed.stdout or "").strip()
        logging.debug("'%s' exited with code %s on '%s':\n%s",
                      jarsigner, completed.returncode, jar_path, output)
        raise JarSignatureError(
            "The CheckVU JAR signature is not valid. '{0}' exited with code {1}:\n{2}"
            .format(jarsigner, completed.returncode, _without_entry_lists(output)))


def _without_entry_lists(jarsigner_output):
    """Keep what jarsigner says about the signature, drop what it repeats per entry.

    When a jar carries internal inconsistencies jarsigner lists one line per entry.
    The CheckVU JAR holds about 21000 of them, which buries the dozen lines that say
    why the signature was refused. The untouched output goes to the debug log.
    """
    kept = []
    for is_entry, group in groupby(jarsigner_output.splitlines(), key=_is_entry_line):
        lines = list(group)
        kept.extend(lines if not is_entry else lines[:KEPT_ENTRY_LINES])
        hidden = len(lines) - KEPT_ENTRY_LINES
        if is_entry and hidden > 0:
            kept.append("... and {0} more entries, run with --debug for the full "
                        "jarsigner output".format(hidden))
    return "\n".join(kept)


def _is_entry_line(line):
    """Tell apart the per-entry lines, which jarsigner writes as a dash-prefixed list."""
    return line.lstrip().startswith("-")


def _locate_jarsigner(java_executable):
    """Return a jarsigner able to verify the JAR, or raise when there is none.
    jarsigner is in JDK, not JRE.
    Try beside the executable, if not present, try with PATH
    """
    binaries = os.path.dirname(os.path.abspath(java_executable))
    beside_java = os.path.join(binaries, "jarsigner.exe" if os.name == "nt" else "jarsigner")
    if os.path.isfile(beside_java):
        return beside_java

    on_path = shutil.which("jarsigner")
    if on_path:
        return on_path

    raise JarVerificationUnavailableError(
        "You are using a JRE ('{0}') which does not provide JAR verification tools "
        "(jarsigner is neither next to it nor on the PATH). Please use a JDK for improved "
        "security to check that the JAR is made by Tricentis. Or add option "
        "--unsafe-skip-jar-verification."
        .format(java_executable))

def _check_signer_is_tricentis(cms_signature):
    from cryptography.x509.oid import NameOID

    signer_certificate = _load_signer_certificate(cms_signature)

    organization = signer_certificate.subject.get_attributes_for_oid(
        NameOID.ORGANIZATION_NAME)
    if not organization or organization[0].value != EXPECTED_ORGANIZATION:
        raise JarSignatureError(
            "The CheckVU JAR is signed by an unexpected party: {0}".format(
                signer_certificate.subject.rfc4514_string()))


def _load_signer_certificate(cms_signature):
    """Return the certificate SignerInfo.sid designates, among those the block ships."""
    from asn1crypto import cms
    from cryptography import x509

    try:
        signed_data = cms.ContentInfo.load(cms_signature)["content"]
        signer_identifier = signed_data["signer_infos"][0]["sid"]
        certificates = [choice.chosen for choice in signed_data["certificates"]
                        if choice.name == "certificate"]
    except (ValueError, KeyError, IndexError) as err:
        raise JarSignatureError("Malformed JAR signature block: {0}".format(err))

    for certificate in certificates:
        if signer_identifier.name == "issuer_and_serial_number":
            if (certificate.issuer == signer_identifier.chosen["issuer"]
                    and certificate.serial_number
                    == signer_identifier.chosen["serial_number"].native):
                return x509.load_der_x509_certificate(certificate.dump())
        elif certificate.key_identifier == signer_identifier.chosen.native:
            return x509.load_der_x509_certificate(certificate.dump())

    raise JarSignatureError("Malformed JAR signature: the signer certificate is missing.")
