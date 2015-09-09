#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

import stealth.util.log as logging
import simplejson as json
import hmac
import hashlib


LOG = logging.getLogger(__name__)


def _generate_cache_key(t):
    """Convert a tuple to a cache key."""
    hashval = hmac.new('A_SECRET_KEY'.encode(), t.encode(),
        hashlib.sha256).hexdigest()
    return hashval


def _send_data_to_cache(redis_client, url, token_data):
    """Stores the authentication data to cache

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: URL used for authentication
    :param token_data: json formatted token information to cache.

    :returns: True and cache_key on success, otherwise False and None
    """
    try:
        # Convert the storable format
        cache_data = json.dumps(token_data.token_data, sort_keys=True)

        # Build the cache key and store the value
        # Use the token's expiration time for the cache expiration
        cache_key = _generate_cache_key(cache_data)

        redis_client.set(cache_key, cache_data)
        redis_client.pexpireat(cache_key, token_data.expires_norm)

        return True, cache_key

    except Exception as ex:
        msg = ('Endpoint: Failed to cache the data - Exception: \
            %(s_except)s') % {
            's_except': str(ex),
        }
        LOG.error(msg)
        return False, None


def _retrieve_data_from_cache(redis_client, url, tenant, cache_key):
    """Retrieve the authentication data from cache

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: URL used for authentication
    :param tenant: tenant id of the user
    :param cache_key: client side auth_token for the tenant_id

    :returns: cached user info on success, or None
    """
    if cache_key is None:
        return None

    cached_data = None
    try:
        # Look up the token from the cache
        cached_data = redis_client.get(cache_key)

    except Exception:
        LOG.debug(('Failed to retrieve data to cache for key %(s_key)s') % {
            's_key': cache_key
        })
        return None

    if cached_data is not None:
        # So 'data' can be used in the exception handler...
        data = None

        try:
            return json.loads(cached_data)

        except Exception as ex:
            # The cached object didn't match what we expected
            msg = ('Endpoint: Stored Data does not contain any credentials - '
                'Exception: %(s_except)s; Data: $(s_data)s') % {
                's_except': str(ex),
                's_data': str(cached_data)
            }
            LOG.error(msg)
            return None
    else:
        LOG.debug(('No data in cache for key %(s_key)s') % {
            's_key': cache_key
        })
        # It wasn't cached
        return None
