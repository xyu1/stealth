import stealth
from stealth.common import context
from stealth.common import local


def TransactionidHook(req, resp, params):
    transaction = context.RequestContext()
    setattr(local.store, 'context', transaction)
    stealth.context.transaction = transaction
    resp.set_header('Transaction-ID', stealth.context.transaction.request_id)
