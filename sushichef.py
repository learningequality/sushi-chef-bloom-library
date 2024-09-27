#!/usr/bin/env python
import requests
import xml.etree.ElementTree as ET
from ricecooker.chefs import SushiChef
from ricecooker.classes.files import BloomPubFile
from ricecooker.classes.licenses import get_license
from ricecooker.classes.nodes import DocumentNode
from ricecooker.exceptions import UnknownLicenseError


class BloomChef(SushiChef):
    channel_info = {
        "CHANNEL_TITLE": "OPDS Bloom Channel",
        "CHANNEL_SOURCE_DOMAIN": "https://bloomlibrary.org/",
        "CHANNEL_SOURCE_ID": "OPDS_BLOOM_CHANNEL",
        "CHANNEL_LANGUAGE": "en",
        "CHANNEL_DESCRIPTION": "Channel for uploading bloom content to Kolibri from Bloom Library",
    }

    def construct_channel(self, **kwargs):
        channel = self.get_channel(**kwargs)

        for content in BLOOM_CONTENT:
            try:
                bloom_node = DocumentNode(
                    title=content['title'],
                    description=content['description'],
                    source_id=f"{content['id']}-{content['title']}",
                    license=get_license(content['license'], copyright_holder=content['rights']),
                    language=content['language'],
                    files=[
                        BloomPubFile(
                            path=content['bloom'],
                            language=content['language'],
                        )
                    ],
                    thumbnail=content['thumbnail']
                )
                channel.add_child(bloom_node)
            except UnknownLicenseError as e:
                print(e)

            except Exception as e:
                print(e)

        return channel


class OPDSClient:

    def __init__(self):
        self.base_url = "https://api.bloomlibrary.org/v1/opds"
        self.account_key = ""
        self.api_key = ""

    def fetch_data(self, lang="en", minimalnavlinks=True, epub=False, organizeby=False):
        params = {
            # "key": f"{self.account_key}:{self.api_key}",
            "lang": lang,
            "minimalnavlinks": minimalnavlinks,
            "epub": epub
        }

        if (organizeby):
            params["organizeby"] = "language"

        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            return response.content
        else:
            response.raise_for_status()

    def parse_data(self, xml_data):
        root = ET.fromstring(xml_data)
        entries = []
        ids = set()

        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "dcterms": "http://purl.org/dc/terms/",
            "bloom": "https://bloomlibrary.org/opds",
            "opds": "http://opds-spec.org/2010/catalog"
        }

        for entry in root.findall('.//atom:entry', namespaces):
            rights = entry.find('dcterms:rights', namespaces).text if entry.find('dcterms:rights', namespaces) is not None else None
            license_code = entry.find('dcterms:license', namespaces).text if entry.find('dcterms:license', namespaces) is not None else None
            thumbnail = entry.find('.//atom:link[@rel="http://opds-spec.org/image"]', namespaces).attrib.get(
                'href') if entry.find('.//atom:link[@rel="http://opds-spec.org/image"]', namespaces) is not None else None
            bloom_url = entry.find('.//atom:link[@type="application/bloompub+zip"]', namespaces).attrib.get(
                'href') if entry.find('.//atom:link[@type="application/bloompub+zip"]', namespaces) is not None else None
            id = entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) is not None else None
            if not bloom_url:
                continue

            try:
                rights = rights.split(", ")[1]
            except:
                continue

            try:
                license_code = license_code.upper()
                license_code = license_code[:2] + " " + license_code[3:]
            except:
                pass

            try:
                thumbnail = thumbnail.split("?")[0]
            except:
                pass
            if id not in ids:
                entry_data = {
                    "id": id,
                    "title": entry.find('atom:title', namespaces).text if entry.find('atom:title', namespaces) is not None else None,
                    "thumbnail": thumbnail,
                    "bloom": bloom_url,
                    "license": license_code,
                    "rights": rights,
                    "language": entry.find('dcterms:language', namespaces).text if entry.find('dcterms:language', namespaces) is not None else None,
                    "description": entry.find('dcterms:subject', namespaces).text if entry.find('dcterms:subject', namespaces) is not None else None,
                }

                entries.append(entry_data)
                ids.add(id)

        return entries


if __name__ == "__main__":
    """
    Run this script on the command line using:
        python sushichef.py  --token=YOURTOKENHERE9139139f3a23232
    """
    chef = BloomChef()
    api_client = OPDSClient()
    xml_data = api_client.fetch_data(lang="en-GB")
    BLOOM_CONTENT = api_client.parse_data(xml_data)
    chef.main()
