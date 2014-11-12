import os, urlparse

def get_request_host(environ): # TODO: this function should be moved to a different module in lda-clientlib (e.g., clientutils.py)
    return environ.get('HTTP_CE_RESOURCE_HOST') or environ.get('HTTP_HOST')

# This class implements a URL Policy where the tenant is part of (or derived from) the hostname (e.g., http://cloudsupplements.cloudapps4.me/cat/1.2)
class HostnameTenantURLPolicy():
    def construct_url(self, hostname, tenant=None, namespace=None, document_id=None, extra_segments=None, query_string=None):
        # hostname is the request hostname. If the hostname is null we are building a relative url.
        # The caller is responsible for assuring that the hostname is compatible with the tenant.
        if tenant:
            hostname_and_port = hostname.split(':')
            hostname_parts = hostname_and_port[0].split('.')
            if hostname_parts[0] != tenant:
                if len(hostname_parts) > 1 and hostname_parts[1] != tenant:
                    hostname_parts[0] = tenant.lower()
                    new_hostname = '.'.join(hostname_parts)
                else:
                    new_hostname = tenant
                hostname_and_port[0] = new_hostname
                hostname = ':'.join(hostname_and_port)
        if document_id is not None:
            parts = ['http:/', hostname, namespace, document_id] if hostname is not None else ['', namespace, document_id]
            if extra_segments is not None:
                parts.extend(extra_segments)
        else:
            if extra_segments is not None:
                raise ValueError('if document_id is None, extra_segments must also be None')
            if namespace is not None:
                parts = ['http:/', hostname, namespace] if hostname is not None else ['', namespace]
            else:
                parts = ['http:/', hostname, ''] if hostname is not None else ['','']
        result =  '/'.join(parts)
        if query_string:
            return '?'.join((result, query_string))
        else:
            return result

    def get_tenant(self, netloc, path):
        if netloc is not None:
            tenant = netloc.split(':')[0].split('.')[0].lower()
        else:
            tenant = None
        return tenant
            
    def get_url_components(self, environ):
        request_host = get_request_host(environ)
        path = environ['PATH_INFO']
        tenant = self.get_tenant(request_host, path)
        path_parts, namespace, document_id, extra_path_segments = self.parse_path(path)
        return (tenant, namespace, document_id, extra_path_segments, path, path_parts, request_host, environ['QUERY_STRING'])

    def parse_path(self, path):
        path_parts = path.split('/')
        namespace = document_id = extra_path_segments = None
        if len(path_parts) > 1 and path_parts[-1] != '': #trailing /
            namespace = path_parts[1]
            if len(path_parts) > 2:
                document_id = path_parts[2]
                if len(path_parts) > 3:
                    extra_path_segments = path_parts[3:]  
        return path_parts, namespace, document_id, extra_path_segments
        
    def parse(self, url):
        parse_rslt = urlparse.urlparse(str(url))
        path_parts, namespace, document_id, extra_path_segments = self.parse_path(parse_rslt.path)
        return namespace, document_id, extra_path_segments, parse_rslt
    
if __name__ == '__main__':
    # run a few tests
    url_policy = HostnameTenantURLPolicy()
    print url_policy.construct_url('cloudsupplements.cloudapps4.me', 'cloudsupplements', 'cat', '1.2')
    print url_policy.construct_url('cloudsupplements.cloudapps4.me', 'cloudsupplements', 'cat')
    print url_policy.construct_url('cloudsupplements.cloudapps4.me', 'cloudsupplements')    
    print url_policy.construct_url(None, 'cloudsupplements', 'cat', '1.2')
    print url_policy.construct_url(None, 'cloudsupplements', 'cat')
    print url_policy.construct_url(None, 'cloudsupplements')    
    
    tenant, namespace, document_id, extra_path_segments, path, path_parts, hostname, query_string = \
        url_policy.get_url_components({'PATH_INFO': '/cat/1.2', 'HTTP_HOST': 'cloudsupplements.cloudapps4.me', 'QUERY_STRING': None})
    print url_policy.construct_url(hostname, tenant, namespace, document_id)
    
    tenant, namespace, document_id, extra_path_segments, path, path_parts, hostname, query_string = \
        url_policy.get_url_components({'PATH_INFO': '/cat', 'HTTP_HOST': 'cloudsupplements.cloudapps4.me', 'QUERY_STRING': None})
    print url_policy.construct_url(hostname, tenant, namespace, document_id)

    tenant, namespace, document_id, extra_path_segments, path, path_parts, hostname, query_string = \
        url_policy.get_url_components({'PATH_INFO': '/', 'HTTP_HOST': 'cloudsupplements.cloudapps4.me', 'QUERY_STRING': None})
    print url_policy.construct_url(hostname, tenant, namespace, document_id)
