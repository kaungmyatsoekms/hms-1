# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HMS - Accounting',
    'version': '1.1',
    'category': 'Localization',
    'description': """
This is the base module to manage the HMS accounting chart in Odoo.
==============================================================================

Install some HMS chart of accounts.
    """,
    'depends': [
        'account',
    ],
    'data': [
        'data/l10n_mm_coa.xml',
        'data/account.account.template.csv',
        'data/l10n_mm_coa_post.xml',
    ],
    'demo': [
        'demo/account_bank_statement_demo.xml',
        'demo/account_invoice_demo.xml',
        'demo/account_reconcile_model.xml',
    ],
    'uninstall_hook': 'uninstall_hook',
}
