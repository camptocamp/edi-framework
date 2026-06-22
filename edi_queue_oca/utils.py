# Copyright 2020 ACSONE SA
# Copyright 2023 Camptocamp
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta

import pytz

from odoo import fields

from odoo.addons.queue_job.job import identity_exact_hasher


def exchange_record_job_identity_exact(job_):
    hasher = identity_exact_hasher(job_)
    # Include files checksum
    hasher.update(
        str(sorted(job_.recordset.mapped("exchange_filechecksum"))).encode("utf-8")
    )
    return hasher.hexdigest()


def eta_float_to_utc(env, eta_time):
    """Convert a decimal-hour ETA to the next occurrence as a naive UTC datetime.

    ``eta_time`` is a float in [0, 24[ where the fractional part represents
    minutes (e.g. 22.5 → 22:30, 0.0 → 00:00 midnight). The target is expressed
    in the current user's timezone and rolled forward by one day when the time
    has already passed today.

    Returns a naive UTC datetime suitable for ``queue.job`` ``eta`` param.
    """
    # Use timedelta from midnight rather than datetime.replace(hour=...) so that
    # values near 24.0 (e.g. 23.992 → 1440 total minutes) wrap cleanly to 00:00
    # the next day instead of crashing with ValueError: hour must be in 0..23.
    total_minutes = round(eta_time * 60) % 1440
    user_tz = pytz.timezone(env.user.tz or "UTC")
    utc_tz = pytz.UTC
    now_utc = fields.Datetime.now().replace(tzinfo=utc_tz)
    now_user = now_utc.astimezone(user_tz)
    midnight = now_user.replace(hour=0, minute=0, second=0, microsecond=0)
    target_user = midnight + timedelta(minutes=total_minutes)
    if target_user <= now_user:
        target_user += timedelta(days=1)
    return target_user.astimezone(utc_tz).replace(tzinfo=None)
