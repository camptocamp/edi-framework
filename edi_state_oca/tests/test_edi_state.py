# Copyright 2023 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo_test_helper import FakeModelLoader

from odoo import exceptions

from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase


class TestEDIState(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import EDIStateConsumerFake

        cls.loader.update_registry((EDIStateConsumerFake,))
        cls.consumer_model = cls.env[EDIStateConsumerFake._name]
        cls.consumer_record = cls.consumer_model.create(
            {
                "name": "State Test Consumer",
            }
        )
        # Suitable workflow
        cls.wf1_ok = cls.env["edi.state.workflow"].create(
            {
                "name": "WF1",
                "backend_type_id": cls.backend.backend_type_id.id,
                "model_id": cls.env["ir.model"]._get(cls.consumer_record._name).id,
            }
        )
        for i in range(1, 4):
            cls.env["edi.state"].create(
                {"name": f"OK {i}", "code": f"OK_{i}", "workflow_id": cls.wf1_ok.id}
            )
        # Non suitable workflow
        cls.wf2_ko = cls.env["edi.state.workflow"].create(
            {
                "name": "WF2",
                "backend_type_id": cls.backend.backend_type_id.id,
                "model_id": cls.env["ir.model"]._get("res.partner").id,
            }
        )
        for i in range(1, 4):
            cls.env["edi.state"].create(
                {"name": f"KO {i}", "code": f"KO_{i}", "workflow_id": cls.wf2_ko.id}
            )
        cls.exc_type = cls._create_exchange_type(
            name="State test",
            code="state_test",
            direction="output",
            state_workflow_ids=[(6, 0, cls.wf1_ok.ids)],
        )
        vals = {
            "model": cls.consumer_record._name,
            "res_id": cls.consumer_record.id,
        }
        record = cls.backend.create_record("state_test", vals)
        cls.consumer_record._edi_set_origin(record)

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_is_state_valid(self):
        self.assertTrue(self.wf1_ok.is_valid_for_model(self.consumer_model._name))
        self.assertFalse(self.wf1_ok.is_valid_for_model("res.partner"))
        self.assertFalse(self.wf2_ko.is_valid_for_model(self.consumer_model._name))
        self.assertTrue(self.wf2_ko.is_valid_for_model("res.partner"))

    def test_mixin(self):
        self.assertFalse(self.consumer_record.edi_state_id)
        self.assertFalse(self.consumer_record.edi_state_workflow_id)
        for state in self.wf1_ok.state_ids:
            self.consumer_record._edi_set_state(state)
            self.assertEqual(self.consumer_record.edi_state_id, state)
        for state in self.wf2_ko.state_ids:
            with self.assertRaisesRegex(
                exceptions.UserError, f"State {state.name} not allowed"
            ):
                self.consumer_record._edi_set_state(state)

    def test_check_is_default(self):
        self.wf2_ko.state_ids[0].is_default = True
        with self.assertRaisesRegex(
            exceptions.UserError, "Only one state per workflow"
        ):
            self.wf2_ko.state_ids[1].is_default = True
