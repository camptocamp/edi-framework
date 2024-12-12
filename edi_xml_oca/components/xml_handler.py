# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import xmltodict
from lxml import etree

from odoo import modules
from odoo.exceptions import UserError
from odoo.tools import validate_xml_from_attachment

from odoo.addons.component.core import Component


class XMLHandler(Component):
    """Validate and parse XML."""

    _name = "edi.xml.handler"
    _inherit = "edi.component.base.mixin"
    _usage = "edi.xml"

    _work_context_validate_attrs = ["schema_path"]

    def __init__(self, work_context):
        super().__init__(work_context)
        for key in self._work_context_validate_attrs:
            if not hasattr(work_context, key):
                raise AttributeError(f"`{key}` is required for this component!")

        self.schema_path, self.schema = self._get_xsd_schema()

    def _get_xsd_schema(self):
        """Lookup and parse the XSD schema."""
        try:
            mod_name, path = self.work.schema_path.split(":")
        except ValueError as exc:
            raise ValueError("Path must be in the form `module:path`") from exc

        schema_path = modules.get_resource_path(mod_name, path)
        with open(schema_path, "rb") as schema_file:
            return schema_path, etree.XMLSchema(etree.parse(schema_file))

    def _xml_string_to_dict(self, xml_string):
        """Read xml_content and return a data dict.

        :param xml_string: str of XML file
        """
        return xmltodict.parse(xml_string)["xs:element"]

    def parse_xml(self, file_content):
        """Read XML content.
        :param file_content: unicode str of XML file
        :return: dict with final data
        """
        tree = etree.XML(file_content.encode("utf-8"))
        xml_string = etree.tostring(tree).decode("utf-8")
        return self._xml_string_to_dict(xml_string)

    def validate(self, xml_content, raise_on_fail=False):
        """Validate XML content against XSD schema.

        Raises `etree.DocumentInvalid` if `raise_on_fail` is True.

        :param xml_content: str containing xml data to validate
        :raise_on_fail: turn on/off validation error exception on fail

        :return:
            * None if validation is ok
            * error string if `raise_on_fail` is False
        """
        xsd_name = self.schema_path
        xml_content = (
            xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        )
        try:
            validate_xml_from_attachment(self.env, xml_content, xsd_name)
        except UserError as exc:
            if raise_on_fail:
                raise exc
            return str(exc)
