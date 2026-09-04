import os
import shutil
import subprocess
import zipfile

from neoload_cli_lib import cli_exception, resources

CMS_SIGNATURE_ENTRY = "META-INF/NEOLOAD_.RSA"
EXPECTED_ORGANIZATION = "Tricentis GmbH"
CERTIFICATE_NAMESPACE = "resources.certs"
TRUSTED_ROOT_KEYSTORE = "globalsign-code-signing-root-r45.jks"

class JarSignatureError(cli_exception.CliException):
    pass


def verify_signed_by_tricentis(jar_path, java_executable):
    """Raise JarSignatureError unless
     - jar signature is verified against trusted root
     - subject DN is Tricentis GmbH
    """
    try:
        archive = zipfile.ZipFile(jar_path)
    except (OSError, zipfile.BadZipFile) as err:
        raise JarSignatureError("'{0}' is not a readable JAR: {1}".format(jar_path, err))

    with archive as jar:
        cms_signature = _read_cms_signature(jar)

    _run_jarsigner(jar_path, java_executable)
    _check_signer_is_tricentis(cms_signature)


def _read_cms_signature(jar):
    """Read the signature block jarsigner wrote at META-INF/NEOLOAD_.RSA."""
    try:
        return jar.read(CMS_SIGNATURE_ENTRY)
    except KeyError:
        raise JarSignatureError(
            "The CheckVU JAR is not signed: no signature block '{0}' found"
            .format(CMS_SIGNATURE_ENTRY))


def _run_jarsigner(jar_path, java_executable):
    """Let the JDK verify the signature against the root shipped with this package.
    Verification is strict (validates whole cert chain, no unsigned entries, no
    modifications)"""
    jarsigner = _locate_jarsigner(java_executable)

    with resources.get_resource_as_path(CERTIFICATE_NAMESPACE, TRUSTED_ROOT_KEYSTORE) as truststore:
        command = [jarsigner, "-verify", "-strict", "-keystore", str(truststore), jar_path]
        try:
            completed = subprocess.run(command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       universal_newlines=True,
                                       errors="replace")
        except OSError as err:
            raise JarSignatureError(
                "Unable to run '{0}' to verify the CheckVU JAR: {1}".format(jarsigner, err))

    if completed.returncode != 0:
        raise JarSignatureError(
            "The CheckVU JAR signature is not valid. '{0}' exited with code {1}:\n{2}"
            .format(jarsigner, completed.returncode, (completed.stdout or "").strip()))


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

    raise JarSignatureError(
        "jarsigner is needed to verify the CheckVU JAR signature, but is neither next to "
        "'{0}' nor on the PATH. It ships with a JDK, not with a JRE. Point --java at a "
        "JDK, put one on the PATH, or run with --unsafe-skip-jar-verification to skip the check"
        "(only if you use a local and already verified JAR)."
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
