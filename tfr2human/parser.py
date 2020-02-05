import warnings
warnings.filterwarnings('ignore',category=FutureWarning)
import tensorflow as tf
import numpy as np
#
# CONFIG
#
COMPRESSION_TYPE='GZIP'
PARALLEL_FILE_READS=5
PARALLEL_PARSE_CALLS=2
IMAGE_DEFAULTS={
    'dtype': tf.float32,
    'default': None
}
DATA_DEFAULTS={
    'dtype': tf.string,
    'dims': (),
    'default': 0,
    'defaults': {
        tf.string: ''
    }
}




#
# TFRParser
#
class TFRParser(object):
    """ Parse TFRecords as dictionaries and numpy arrays 
    """
    IMAGE='image'
    DATA='data'


    @staticmethod
    def read_dataset(
            files,
            compression=COMPRESSION_TYPE,
            parallel_reads=PARALLEL_FILE_READS,
            parallel_calls=PARALLEL_PARSE_CALLS):
        if isinstance(files,str):
            files=[files]
        return tf.data.TFRecordDataset(
                    filenames=files,
                    compression_type=compression,
                    num_parallel_reads=parallel_reads)


    def __init__(self, 
            dataset,
            specs=None,
            band_specs=None,
            dims=None,
            image_defaults=IMAGE_DEFAULTS,
            data_defaults=DATA_DEFAULTS,
            compression=COMPRESSION_TYPE,
            parallel_reads=PARALLEL_FILE_READS,
            parallel_calls=PARALLEL_PARSE_CALLS):
        if dims:
          image_defaults['dims']=dims
        self.image_defaults=image_defaults
        self.data_defaults=data_defaults
        self.specs=specs
        self.keys=[k for k in specs or []]
        self.band_specs=band_specs
        self.bands=[b for b in band_specs or []]
        self.dataset=self._dataset(
            dataset,
            compression,
            parallel_reads,
            parallel_calls)


    def image(self,element,bands=None,dtype=None):
        if not bands:
            bands=self.bands
        if isinstance(bands,(int,str)):
            bands=[bands]
        im_dict={b: element[b].numpy() for b in bands}
        im=np.stack([im_dict[b] for b in bands])
        if dtype:
            im=im.astype(dtype)
        return im


    def data(self,element,keys=None,pop_single=True):
        if not keys:
            keys=self.keys
        if isinstance(keys,(int,str)):
            keys=[keys]        
        out={ k: self._clean(tf.get_static_value(element[k])) for k in keys }
        if pop_single and (len(out)==1):
            out=out[keys[0]]
        return out


    #
    # INTERNAL
    #
    def _dataset(self,dataset,compression,parallel_reads,parallel_calls):
        dataset=self._init_dataset(dataset,compression,parallel_reads)
        return self._get_parsed_dataset(dataset,parallel_calls)


    def _init_dataset(self,dataset,compression,parallel_reads):
        if isinstance(dataset,(str,list,tuple)):
            dataset=TFRParser.read_dataset(dataset,compression,parallel_reads)
        return dataset


    def _get_parsed_dataset(self,dataset,parallel_calls):
        return dataset.map(
                self._parse_feature, 
                num_parallel_calls=parallel_calls)


    def _parse_feature(self,feat):
        feature_spec={}
        if self.band_specs:
            for spec in self.band_specs:
                key,dims,dtype,default=self._feature_args(
                    spec,
                    self.band_specs,
                    TFRParser.IMAGE)
                feature_spec[key]=tf.io.FixedLenFeature(
                    dims, 
                    dtype, 
                    default_value=default)
        if self.specs:
            for spec in self.specs:
                key,dims,dtype,default=self._feature_args(
                    spec,
                    self.specs,
                    TFRParser.DATA)
                feature_spec[key]=tf.io.FixedLenFeature(
                    dims, 
                    dtype, 
                    default_value=default)
        return tf.io.parse_single_example(feat, feature_spec)


    def _feature_args(self,spec,specs,typ):
        if isinstance(specs,dict):
            cfig=specs[spec]
            if not isinstance(cfig,dict):
                cfig={ 'dtype': cfig }
        else:
            cfig={}
        key=cfig.get('key',spec)
        if typ==TFRParser.IMAGE:
            dflt=self.image_defaults
        else:
            dflt=self.data_defaults
        dims=cfig.get('dims',dflt.get('dims'))
        dtype=cfig.get('dtype',dflt.get('dtype'))
        default=cfig.get('default',dflt.get('default'))
        defaults=cfig.get('defaults',dflt.get('defaults'))
        if defaults:
            default=defaults.get(dtype,default)
        return key, dims, dtype, default
    

    def _clean(self,value):
      if isinstance(value,bytes):
              value=value.decode("utf-8")
      return value
