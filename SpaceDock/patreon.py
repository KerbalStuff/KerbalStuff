from SpaceDock.config import _cfg
from SpaceDock.celery import update_patreon
import celery
import redis
import time
import json

donation_cache = redis.Redis(db=0)

def GetDonationAmount():
    last_update_time = float(donation_cache.get('patreon_update_time').decode('utf-8'))
    donation_amount = int(donation_cache.get('patreon_donation_amount').decode('utf-8'))
    request_update = False

    if donation_amount is None:
        donation_amount = 0
        donation_cache.set('patreon_donation_amount', 0)
    
    if last_update_time is None:
        request_update = True
    else:
        time_delta = time.time() - last_update_time
        #Update every 10 minutes
        if time_delta > 600:
            request_update = True
    
    if request_update:
        update_patreon.delay()
    
    return donation_amount
