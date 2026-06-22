# Copyright 2020 ACSONE
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime

import pytz
from freezegun import freeze_time

from odoo.exceptions import ValidationError

from odoo.addons.edi_core_oca.tests.common import EDIBackendCommonTestCase
from odoo.addons.edi_queue_oca.utils import eta_float_to_utc
from odoo.addons.queue_job.delay import DelayableRecordset


class EDIRecordTestCase(EDIBackendCommonTestCase):
    def _make_record(self):
        return self.backend.create_record(
            "test_csv_input",
            {"model": self.partner._name, "res_id": self.partner.id},
        )

    def _get_delayed(self, record):
        delayed = record.with_context(queue_job__no_delay=False).with_delay()
        # Suppress "prepared but never delayed" warning
        delayed.delayable._generated_job = object()
        return delayed

    def _get_job_eta(self, record):
        return self._get_delayed(record).delayable.eta

    def test_with_delay_override(self):
        record = self._make_record()
        parent_channel = self.env["queue.job.channel"].create(
            {
                "name": "parent_test_chan",
                "parent_id": self.env.ref("queue_job.channel_root").id,
            }
        )
        channel = self.env["queue.job.channel"].create(
            {"name": "test_chan", "parent_id": parent_channel.id}
        )
        self.exchange_type_in.job_channel_id = channel
        self.exchange_type_in.job_priority = 5
        self.exchange_type_in.eta_enabled = True
        self.exchange_type_in.eta_time = 22.0
        delayed = self._get_delayed(record)
        job_eta = delayed.delayable.eta
        utc_tz = pytz.UTC
        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        target_22h_user = datetime.now(user_tz).replace(
            hour=22, minute=0, second=0, microsecond=0
        )
        expected_eta = target_22h_user.astimezone(utc_tz).replace(tzinfo=None)
        self.assertEqual(job_eta, expected_eta)
        self.assertTrue(isinstance(delayed, DelayableRecordset))
        self.assertEqual(delayed.recordset, record)
        self.assertEqual(delayed.delayable.channel, "root.parent_test_chan.test_chan")
        self.assertEqual(delayed.delayable.priority, 5)

    def test_eta_disabled_no_eta_applied(self):
        """eta_enabled=False: no ETA is set regardless of eta_time value."""
        self.exchange_type_in.eta_time = 22.0
        # eta_enabled defaults to False
        record = self._make_record()
        self.assertIsNone(self._get_job_eta(record))

    def test_eta_time_invalid_not_24h(self):
        with self.assertRaises(ValidationError):
            self.exchange_type_in.write({"eta_enabled": True, "eta_time": 28})

    @freeze_time("2024-01-15 20:00:00")
    def test_eta_scheduled_same_day(self):
        """ETA not yet reached today: job lands on the same calendar day."""
        self.env.user.tz = "UTC"
        self.exchange_type_in.eta_enabled = True
        self.exchange_type_in.eta_time = 22.0
        record = self._make_record()
        self.assertEqual(
            self._get_job_eta(record),
            datetime(2024, 1, 15, 22, 0, 0),
        )

    @freeze_time("2024-01-15 23:00:00")
    def test_eta_scheduled_next_day(self):
        """ETA already passed today: job rolls over to the next calendar day."""
        self.env.user.tz = "UTC"
        self.exchange_type_in.eta_enabled = True
        self.exchange_type_in.eta_time = 22.0
        record = self._make_record()
        self.assertEqual(
            self._get_job_eta(record),
            datetime(2024, 1, 16, 22, 0, 0),
        )

    @freeze_time("2024-01-15 20:00:00")
    def test_eta_midnight_schedules_next_day(self):
        """eta_time=0.0 (midnight) schedules for the next 00:00 in user TZ."""
        self.env.user.tz = "UTC"
        self.exchange_type_in.eta_enabled = True
        self.exchange_type_in.eta_time = 0.0
        record = self._make_record()
        self.assertEqual(
            self._get_job_eta(record),
            datetime(2024, 1, 16, 0, 0, 0),
        )

    @freeze_time("2024-01-15 20:00:00")
    def test_eta_near_midnight_no_overflow(self):
        """Values just below 24 must not crash with ValueError at runtime."""
        self.env.user.tz = "UTC"
        # 23.992 * 60 = 1439.52 → round → 1440 → % 1440 = 0 → midnight next day
        result = eta_float_to_utc(self.env, 23.992)
        self.assertEqual(result, datetime(2024, 1, 16, 0, 0, 0))
