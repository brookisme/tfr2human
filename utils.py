from googleapiclient.discovery import build
from retrying import retry
import rasterio as rio


DEFAULT_MIME_TYPE='application/json'
TMP_NAME='tmp'
DEFAULT_IMAGE_MIME_TYPE='image/tiff'
CSV_MIME_TYPE='text/csv'
WAIT_EXP_MULTIPLIER=1000
WAIT_EXP_MAX=1000
STOP_MAX_ATTEMPT=7


def gcs_service(service=None):
    """ get gcloud storage client if it does not already exist """
    if not service:
        service=build('storage', 'v1')
    return service


@retry(
    wait_exponential_multiplier=WAIT_EXP_MULTIPLIER, 
    wait_exponential_max=WAIT_EXP_MAX,
    stop_max_attempt_number=STOP_MAX_ATTEMPT)
def save_to_gcs(
        src,
        dest,
        mtype=DEFAULT_MIME_TYPE,
        folder=None,
        bucket=None,
        service=None,
        return_path=True):
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
        * return_path<bool>: 
            - if true return gc://{bucket}/{path}
            - else return response from request  
    """
    media = MediaFileUpload(
        src, 
        mimetype=mtype,
        resumable=True)
    path, bucket=_gcs_path_and_bucket(dest,folder,bucket)
    request=gcs_service(service).objects()
                                .insert(
                                    bucket=bucket, 
                                    name=path,
                                    media_body=media)
    response=None
    while response is None:
        _, response=request.next_chunk()
    if return_path:
        return f'gs://{bucket}/{path}'
    else:
        return response


def image_to_gcs(
    im,
    dest,
    profile=None,
    mtype=DEFAULT_IMAGE_MIME_TYPE,
    tmp_name=TMP_NAME,
    folder=None,
    bucket=None,
    service=None,
    return_path=True):
    """
    """
    if not isinstance(im,str):
        with rio.open(tmp_name,'w',**profile) as dst:
                dst.write(im)
        im=tmp_name
    return save_to_gcs(
        src=im,
        dest=dest,
        mtype=mtype,
        folder=folder,
        bucket=bucket,
        service=service,
        return_path=return_path)


def csv_to_gcs(
    dataset,
    dest,
    tmp_name=TMP_NAME,
    folder=None,
    bucket=None,
    service=None,
    return_path=True):
    """
    """  
    if not isinstance(dataset,str):
        dataset.to_csv(tmp_name,index=False)
        dataset=tmp_name
    return save_to_gcs(
        src=dataset,
        dest=dest,
        mtype=CSV_MIME_TYPE,
        folder=folder,
        bucket=bucket,
        service=service,
        return_path=return_path)



#
# INTERNAL
#
def _gcs_path_and_bucket(dest,folder,bucket):
    if not bucket:
        parts=dest.split('/')
        bucket=parts[0]
        dest='/'.join(parts[1:])
    if folder:
        dest='{}/{}'.format(folder,dest)
    return dest, bucket



