import datetime
import os
import zipfile
from unittest import mock

import pytest
from asn1crypto import cms as asn1_cms
from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from neoload_cli_lib import jar_signature


def signature_block(organization):
    """Builds a CMS block similar to what jarsigner writes. It allows to
    test organization verification. Signature itself is empty, jarsigner
    will be mocked for tests"""
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, "CheckVU test signer"),
    ])
    certificate = asn1_x509.Certificate.load(
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(4242)
        .not_valid_before(datetime.datetime(2020, 1, 1))
        .not_valid_after(datetime.datetime(2040, 1, 1))
        .sign(key, hashes.SHA256())
        .public_bytes(serialization.Encoding.DER))

    return asn1_cms.ContentInfo({
        'content_type': 'signed_data',
        'content': asn1_cms.SignedData({
            'version': 'v1',
            'digest_algorithms': [{'algorithm': 'sha256'}],
            'encap_content_info': {'content_type': 'data'},
            'certificates': [asn1_cms.CertificateChoices(
                name='certificate', value=certificate)],
            'signer_infos': [asn1_cms.SignerInfo({
                'version': 'v1',
                'sid': asn1_cms.SignerIdentifier(
                    name='issuer_and_serial_number',
                    value={'issuer': certificate.issuer,
                           'serial_number': certificate.serial_number}),
                'digest_algorithm': {'algorithm': 'sha256'},
                'signature_algorithm': {'algorithm': 'sha256_ecdsa'},
                'signature': b'',
            })],
        }),
    }).dump()


def jar_signed_by(tmp_path, organization):
    return jar_containing(tmp_path, signature_block(organization))


def jar_containing(tmp_path, cms_signature):
    jar = tmp_path / "checkvu.jar"
    with zipfile.ZipFile(jar, "w") as archive:
        archive.writestr("com/neotys/checkvu/Main.class", b"")
        if cms_signature is not None:
            archive.writestr(jar_signature.CMS_SIGNATURE_ENTRY, cms_signature)
    return str(jar)


@pytest.fixture
def jarsigner():
    """Mock jarsigner as returning exit 0 (success)"""
    with mock.patch.object(jar_signature, '_locate_jarsigner', return_value="jarsigner"), \
            mock.patch('subprocess.run',
                       return_value=mock.Mock(returncode=0, stdout="jar verified.")) as run:
        yield run


class TestVerifySignedByTricentis:

    def test_accepts_valid_jar(self, tmp_path, jarsigner):
        jar = jar_signed_by(tmp_path, "Tricentis GmbH")
        jar_signature.verify_signed_by_tricentis(jar, "java")

    def test_rejects_a_jar_signed_by_someone_else(self, tmp_path, jarsigner):
        jar = jar_signed_by(tmp_path, "Evil Corp")
        with pytest.raises(jar_signature.JarSignatureError) as err:
            jar_signature.verify_signed_by_tricentis(jar, "java")
        assert "unexpected party" in str(err.value)
        assert "Evil Corp" in str(err.value)

    def test_rejects_an_unsigned_jar(self, tmp_path, jarsigner):
        jar = jar_containing(tmp_path, None)
        with pytest.raises(jar_signature.JarSignatureError) as err:
            jar_signature.verify_signed_by_tricentis(jar, "java")
        assert "not signed" in str(err.value)

    def test_rejects_a_jar_jarsigner_refuses(self, tmp_path, jarsigner):
        jarsigner.return_value = mock.Mock(returncode=4, stdout="chain not validated")
        jar = jar_signed_by(tmp_path, "Tricentis GmbH")
        with pytest.raises(jar_signature.JarSignatureError) as err:
            jar_signature.verify_signed_by_tricentis(jar, "java")
        assert "exited with code 4" in str(err.value)
        assert "chain not validated" in str(err.value)

    def test_rejects_a_file_that_is_not_a_jar(self, tmp_path, jarsigner):
        not_a_jar = tmp_path / "checkvu.jar"
        not_a_jar.write_text("not a zip")
        with pytest.raises(jar_signature.JarSignatureError) as err:
            jar_signature.verify_signed_by_tricentis(str(not_a_jar), "java")
        assert "not a readable JAR" in str(err.value)

    def test_rejects_a_signature_block_that_is_not_cms(self, tmp_path, jarsigner):
        jar = jar_containing(tmp_path, b"garbage")
        with pytest.raises(jar_signature.JarSignatureError) as err:
            jar_signature.verify_signed_by_tricentis(jar, "java")
        assert "Malformed JAR signature" in str(err.value)

    def test_verifies_strictly_against_the_root_shipped_with_the_package(self, tmp_path,
                                                                        jarsigner):
        jar = jar_signed_by(tmp_path, "Tricentis GmbH")
        jar_signature.verify_signed_by_tricentis(jar, "java")

        command = jarsigner.call_args.args[0]
        assert command[:4] == ["jarsigner", "-verify", "-strict", "-keystore"]
        assert os.path.isfile(command[4])
        assert os.path.basename(command[4]) == jar_signature.TRUSTED_ROOT_KEYSTORE
        assert command[5] == jar


class TestLocateJarsigner:

    def _java_home(self, tmp_path):
        binaries = tmp_path / "jdk" / "bin"
        binaries.mkdir(parents=True)
        (binaries / "java").write_text("")
        return binaries

    def test_prefers_the_one_next_to_the_java_executable(self, tmp_path):
        binaries = self._java_home(tmp_path)
        beside_java = binaries / ("jarsigner.exe" if os.name == "nt" else "jarsigner")
        beside_java.write_text("")

        located = jar_signature._locate_jarsigner(str(binaries / "java"))

        assert located == str(beside_java)

    def test_falls_back_to_the_path_when_java_is_a_jre(self, tmp_path):
        binaries = self._java_home(tmp_path)
        with mock.patch('shutil.which', return_value="/usr/bin/jarsigner"):
            located = jar_signature._locate_jarsigner(str(binaries / "java"))

        assert located == "/usr/bin/jarsigner"

    def test_fails_when_no_jdk_is_reachable(self, tmp_path):
        binaries = self._java_home(tmp_path)
        with mock.patch('shutil.which', return_value=None):
            with pytest.raises(jar_signature.JarSignatureError) as err:
                jar_signature._locate_jarsigner(str(binaries / "java"))

        assert "JDK" in str(err.value)
