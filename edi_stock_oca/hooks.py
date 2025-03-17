from openupgradelib.openupgrade import logged_query


def post_init_hook(env):
    logged_query(
        env.cr,
        """
        UPDATE stock_picking SET edi_disable_auto =
        CASE
            WHEN state IN ('draft', 'waiting', 'confirmed', 'assigned') THEN TRUE
            ELSE FALSE
        END
        """,
    )


def pre_init_hook(env):
    # Following query is needed when the amount of records
    # causes a MemoryError in the ORM
    logged_query(
        env.cr,
        """
        ALTER TABLE stock_picking ADD COLUMN IF NOT EXISTS
        edi_disable_auto BOOLEAN DEFAULT FALSE;
        """,
    )
