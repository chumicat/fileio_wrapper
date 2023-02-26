import io
import json
import os
import re
import requests
from datetime import datetime, timedelta
from typing import Union, Callable, Literal


class class_or_instancemethod(classmethod):
    """
    Reference: https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod
    """

    def __get__(self, instance, type_):
        descr_get = super().__get__ if instance is None else self.__func__.__get__
        return descr_get(instance, type_)


class Fileio(object):
    url = 'https://file.io/'
    headers = {'accept': 'application/json'}

    def __init__(self, api_key: str) -> None:
        """Constructor of Fileio Class

        Construct Fileio instance with api_key
        Auth needed method have to be called by Fileio instance
        Non-auth needed method can be called by Fileio class directly

        Example:
            fileio = Fileio('XXXXXXX.XXXXXX-XXXXXX-XXXXXX-XXXXXX')

        Args:
            api_key: API Key of file.io account
                You can get API Key of account at https://www.file.io/account/apikeys
        """
        self.api_key = api_key
        self.headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_key),
            # requests won't add a boundary if this header is set when you pass files=
            # 'Content-Type': 'multipart/form-data',
        }

    @class_or_instancemethod
    def __do_request(self, method: Callable, path: str = '', queries: dict = {}, headers: dict = {},
                     files: dict = {}) -> dict:
        """Make a request to file.io

        A private method that formatting request and result

        Args:
            method: Request method to apply [GET, POST, PUT, PATCH, DELETE]
            queries: Dict of query data.
            headers: Dict of header data. No need in general case.
            files: Dict of files data.

        Return:
            Dict loads from result json
            Should always have following Keys: 'success', 'status', 'key'
        """
        # Formatting queries
        queries = ['{}={}'.format(key, val) for key, val in queries.items() if val]
        queries = '?{}'.format('&'.join(queries)) if queries else ''

        # Not use auth if api_key not assigned(as class method)
        # Use auth if api_key assigned(as instance method)
        headers = headers if headers else self.headers

        # Formatting files
        if 'file' not in files:
            pass
        elif files['file'] == '__default':
            del files['file']
        else:
            files['file'] = files['file'] if files['file'] else ''
        if 'expires' not in files:
            pass
        elif files['expires'][1] == '__default':
            del files['expires']
        else:
            files['expires'][1] = files['expires'][1].isoformat() if isinstance(files['expires'][1], datetime) \
                else (datetime.now() + files['expires'][1]).isoformat() if isinstance(files['expires'][1], timedelta) \
                else files['expires'][1] if files['expires'][1] else ''
        if 'maxDownloads' not in files:
            pass
        elif files['maxDownloads'][1] == '__default':
            del files['maxDownloads']
        else:
            files['maxDownloads'][1] = str(files['maxDownloads'][1]) if files['maxDownloads'][1] else ''
        if 'autoDelete' not in files:
            pass
        elif files['autoDelete'][1] == '__default':
            del files['autoDelete']
        else:
            files['autoDelete'][1] = str(files['autoDelete'][1]).lower() if files['autoDelete'][1] else ''
        key = None if path == 'me' else path

        try:
            resp = method(self.url + path + queries, headers=headers, files=files)
            resp = json.loads(
                resp.text if resp.text else '{{"success": true, "status": {}, "key": {} }}'.format(resp.status_code,
                                                                                                   '"{}"'.format(
                                                                                                       key) if key else 'null'))
            return resp
        except ValueError:
            return {
                'success': False,
                'status': 0,
                'code': 'RESULT _ERROR',
                'message': 'Result is not JSON',
                'key': key
            }
        except:
            return {
                'success': False,
                'status': resp.status_code if 'resp' in locals() else 503,
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Not able to connect to file.io server',
                'key': key
            }

    @class_or_instancemethod
    def upload(self, file: str, expires: Union[str, datetime, timedelta] = '__default',
               max_downloads: int = '__default', auto_delete: bool = '__default') -> dict:
        """Uploads files and creates file details

        Upload a file in filesystem to file.io either auth or not

        Example:
            fileio = Fileio('XXXXXXX.XXXXXX-XXXXXX-XXXXXX-XXXXXX')
            result = fileio.upload('myfile.txt')  # upload with auth
            result = Fileio.upload('myfile.txt')  # upload without auth

        Args:
            file: File path to upload. Notice that file size can not be 0.
                "__default" is reserved name, not able to upgrade a file named "__default"
            expires:
                File will be unavailable after expiration date.
                ISO 8601 Format or Count-Down Format "^[1-9][0-9]*[y|Q|M|w|d|h|m|s]$" or None for no expires.
                Free account should always set expires less/equal 1 year
                Default value is '2w' (2 weeks)
                Example (ISO 8601): "20230228T210102" stand for Time = 2023-02-28 21:01:02
                Example (Count-Down): "1y" for 1 year; "80d" for 80 days
                Example (No expires): None
            max_downloads:
                File will be unavailable after downloaded for max_downloads times
                Default value is 1
                Free account should always set max_downloads to 1
            auto_delete:
                Auto-delete file on expiration or max downloads
                Default value is True
                Free account should always set auto_delete to True

        Return:
            A dict of file details
            Should always have following Keys: 'success', 'status', 'key'
            Most useful key-pairs are as follow:
                'success': bool. True if upload success
                'key': str. id of the file
                'link': str. download url of file. This is not a direct link.
        """
        with open(file, 'rb') as f:
            files = {
                'file': f,
                'expires': [None, expires],
                'maxDownloads': [None, max_downloads],
                'autoDelete': [None, auto_delete],
            }
            return self.__do_request(requests.post, files=files)

    def list(self, search: str = None, sort: str = None, offset: int = None, limit: int = None):
        """Get list of files for authorized user

        List files in an file.io accunt. Auth is needed
        Return all item by __default, return particular item with given parameter.

        Example:
            fileio = Fileio('XXXXXXX.XXXXXX-XXXXXX-XXXXXX-XXXXXX')
            resp = fileio.list()
            success = resp['success']
            file_list = resp['nodes']

        Args:
            search: Keyword to search. List item that matched the keyword
            sort: Sort return items list with specific key.
                Only one key can be specified.
                Common used key are such as 'name', 'size', 'expires'
            offset: Return items list start from offset of total item list
            limit: Items count limit of return items list

        Return:
            A dict of file details
            Items list will be stored in key 'nodes'
        """
        queries = {
            'search': search,
            'sort': sort,
            'offset': offset,
            'limit': limit,
        }
        return self.__do_request(requests.get, queries=queries)

    def me(self):
        """Get plan/account details for authorized user

        Get account info, such as "Current account plan", "Storage limit", Uupload size restriction", etc...

        Example:
            fileio = Fileio('XXXXXXX.XXXXXX-XXXXXX-XXXXXX-XXXXXX')
            resp = fileio.me()
            success = resp['success']
            max_storage = resp['maxStorageBytes']
            used_storage = resp['usedStorageBytes']

        Return:
            A dict of account details
        """
        return self.__do_request(requests.get, path='me')

    @class_or_instancemethod
    def download(self, key: str, filepath: str = None):
        """Dlownloads the file identified by key

        Download file with key.
        Return raw byte-type data if filepath parameter didn't assigned
        Return download result if filepath parameter assigned and download file to the filepath

        Args:
            key: key of file in file.io
            filepath: filepath of local filesystem

        Example:
            fileio = Fileio('XXXXXXX.XXXXXX-XXXXXX-XXXXXX-XXXXXX')
            ret_json = Fileio.download('ZDu1og7rOkJq')              # Get raw data if not assigned filepath variable
            raw data = ret_json['content']
            ret_json = Fileio.download('ZDu1og7rOkJq', 'file.txt')  # Save to file if assigned filename with assigned filename
            ret_json = Fileio.download('ZDu1og7rOkJq', 'content/')  # Save to file if assigned exist directory with original filename
            ret_json = fileio.download('ZDu1og7rOkJq')              # Get raw data if not assigned filepath variable
            raw data = ret_json['content']
            ret_json = fileio.download('ZDu1og7rOkJq', 'file.txt')  # Save to file if assigned filename with assigned filename
            ret_json = fileio.download('ZDu1og7rOkJq', 'content/')  # Save to file if assigned exist directory with original filename

        Return:
            Return raw byte-type data if filepath parameter didn't assigned
            Return download result if filepath parameter assigned and download file to the filepath
        """
        headers = self.headers.copy()
        headers['accept'] = '*/*'

        try:
            resp = requests.get(self.url + key, headers=headers)
            filename = re.search('filename=([^;]+);?', resp.headers['content-disposition']).group(1)

            if not filepath:
                return {
                    'success': True,
                    'status': resp.status_code,
                    'key': key,
                    'content': resp.content
                }
            else:
                filename = os.path.join(os.path.dirname(filepath), filename) if os.path.isdir(filepath) else filepath
                with open(filename, 'wb') as f:
                    f.write(resp.content)
                return {
                    'success': True,
                    'status': resp.status_code,
                    'key': key,
                    'path': os.path.dirname(os.path.abspath(filename)),
                    'name': os.path.basename(filename),
                }
        except:
            return {
                'success': False,
                'status': resp.status_code if 'resp' in locals() else 503,
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Not able to connect to file.io server',
                'key': key
            }

    def delete(self, key: str):
        """Deletes the file identified by key for authorized user

        Example:


        Args:
            key: key of file

        Return:
            A dict of result status
        """
        return self.__do_request(requests.delete, path=key)

    def update(self, key: str, file: str = '__default', expires: Union[str, datetime, timedelta] = '__default',
               max_downloads: int = '__default', auto_delete: bool = '__default',
               mode: Literal['replace_all', 'replace_partial'] = 'replace_partial'):
        """Updates the file identified by key for authorized user

        Update a valid key, such as "change file", "extend expire date", "enable auto delete"

        Example:
            TODO

        Args:
            file: File path to upload. Notice that file size can not be 0.
                "__default" is reserved name, not able to update a file named "__default"
            expires:
                File will be unavailable after expiration date.
                ISO 8601 Format or Count-Down Format "^[1-9][0-9]*[y|Q|M|w|d|h|m|s]$" or None for no expires.
                Free account should always set expires less/equal 1 year
                Default value is '2w' (2 weeks)
                Example (ISO 8601): "20230228T210102" stand for Time = 2023-02-28 21:01:02
                Example (Count-Down): "1y" for 1 year; "80d" for 80 days
                Example (No expires): None
            max_downloads:
                File will be unavailable after downloaded for max_downloads times
                Default value is 1
                Free account should always set max_downloads to 1
            auto_delete:
                Auto-delete file on expiration or max downloads
                Default value is True
                Free account should always set auto_delete to True
            mode:
                String either 'replace_all' or 'replace_partial'
                'replace_all' will update all properties even properties didn't assigned
                'replace_partial' will update properties that had assigned value
        """
        f = file if file == '__default' else open(file, 'rb')
        files = {
            'file': f,
            'expires': [None, expires],
            'maxDownloads': [None, max_downloads],
            'autoDelete': [None, auto_delete],
        }
        if isinstance(f, io.IOBase):
            f.close()
        if mode == 'replace_all':
            return self.__do_request(requests.put, path=key, files=files)
        elif mode == 'replace_partial':
            return self.__do_request(requests.patch, path=key, files=files)
        else:
            raise ValueError

