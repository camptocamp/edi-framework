# Copyright 2026 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import BaseCase

from ..utils import data_merge


class TestDataMerge(BaseCase):
    """Merge a sent payload into the stored one."""

    def test_merge_into_nothing(self):
        """Merging into nothing returns the new value."""
        self.assertEqual(data_merge(None, {"a": 1}), {"a": 1})

    def test_merge_primitive(self):
        """A primitive is replaced by the new value."""
        self.assertEqual(data_merge("old", "new"), "new")
        self.assertEqual(data_merge(1, 2), 2)

    def test_merge_dicts(self):
        """Dicts are merged recursively, new keys are added."""
        left = {"a": 1, "nested": {"x": 1, "y": 2}}
        right = {"b": 2, "nested": {"y": 3, "z": 4}}
        self.assertEqual(
            data_merge(left, right),
            {"a": 1, "b": 2, "nested": {"x": 1, "y": 3, "z": 4}},
        )

    def test_merge_lists(self):
        """Lists are appended to, never replaced."""
        self.assertEqual(data_merge([1], [2, 3]), [1, 2, 3])
        self.assertEqual(data_merge([1], 2), [1, 2])

    def test_merge_non_dict_into_dict(self):
        """A non-dict cannot be merged into a dict."""
        with self.assertRaises(ValueError):
            data_merge({"a": 1}, [1])

    def test_merge_unsupported(self):
        """Tuples and other objects are not supported."""
        with self.assertRaises(NotImplementedError):
            data_merge((1,), (2,))
