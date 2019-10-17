from googleapiclient.discovery import build

DEFAULT_MIME_TYPE='application/json'


def gcs_service(service=None):
    """ get gcloud storage client if it does not already exist """
    if not service:
        service=build('storage', 'v1')
    return service
  


def save_to_gcs(
        src,
        dest,
        mtype=DEFAULT_MIME_TYPE,
        folder=None,
        bucket=None,
        service=None,
        return_request=False):
    """ save file to google cloud storage
        * src<str>: source path
        * dest<str>: 
            - file path on google cloud storage
            - if bucket not passed bucket with be assumed to be the first 
              part of the path
        * mtype<str>: mime type
        * folder<str>: prefixed to dest path above
        * bucket<str>: 
            - gcloud bucket
            - if bucket not passed bucket with be assumed to be the first 
              part of the dest path
        * service<google-storage-client|None>: if none, create client
        * return_request<bool>: 
            - if true return gcloud response and request 
              otherwise only return request    
    """
    media = MediaFileUpload(
        src, 
        mimetype=mtype,
        resumable=True)
    if not bucket:
        parts=dest.split('/')
        bucket=parts[0]
        dest='/'.join(parts[1:])
    if folder:
        dest='{}/{}'.format(folder,dest)
    request=gcs_service(service).objects()
                                .insert(
                                    bucket=bucket, 
                                    name=dest,
                                    media_body=media)
    response=None
    while response is None:
        _, response=request.next_chunk()
    if return_request:
        return response, request
    else:
        return response

