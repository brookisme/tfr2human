### TFR2Human

_easy parsing of TFRecords_

---

#### INSTALL

```bash
git clone https://github.com/brookisme/tfr2human.git
pip install -e tfr2human
```

---

#### PARSER

Usage (see complete example at the bottom of this readme):

```python
TFR_LIST=<list of paths to tfrecords>
FEATURE_PROPS=<dictionary of properties and property types>
BANDS=<list of band names or dict describing bands>
SIZE=<DIMENSIONALITY OF BANDS>

parser=tfp.TFRParser(
    TFR_LIST,
    specs=FEATURE_PROPS,
    band_specs=BANDS,
    dims=[SIZE,SIZE])

for i,element in enumerate(parser.dataset)
    ...
    some_image=parser.image(element,bands=SOME_IM_BANDS,dtype=np.uint8)
    some_data=parser.data(element,keys=SOME_KEYS)
```


---

#### UTILS

Here is a quick run down of the methods:

    * get_batches: break datasets into batches. note this is different than TF's [batch](https://www.tensorflow.org/api_docs/python/tf/data/TFRecordDataset#batch) since it returns batches of datasets to be parsed rather than parsing a batch at a time.
    * image_profile: returns an image (rasterio) profile for a given lon/lat/crs/resolution/np.array
    * gcs_service: returns a google cloud storage client
    * save_to_gcs: save generic file to google cloud storage
    * csv/image_to_gcs: save csv/image to google cloud storage

---

#### EXAMPLE

```python
#
# CONFIG
#
NOISY=True
NOISE_REDUCER=10
RESOLUTION=20
SIZE=384
MIN_WATER_RATIO=0.005
MAX_WATER_RATIO=0.96
MAX_WATER_NO_DATA_COUNT=int((SIZE**2)*(0.25))
MAX_S1_NAN_COUNT=int((SIZE**2)*(0.01))
MAX_S1_ZERO_COUNT=int((SIZE**2)*(0.1))

WATER_COLUMNS={
    0: 'no_data_count',
    1: 'not_water_count',
    2: 'water_count'
}


#
# TFR Feature Specs
#
WATER_BANDS=['water']
S1_BANDS=['VV','VH','angle','VV_mean','VH_mean']
BANDS=S1_BANDS+WATER_BANDS

FEATURE_PROPS={
    'tile_id': tf.string,
    'crs': tf.string,
    'year': tf.float32,
    'month': tf.float32,
    'lon': tf.float32,
    'lat': tf.float32,
    'x_offset': tf.float32,
    'y_offset': tf.float32,
    'biome_num': tf.float32,
    'biome_name': tf.string,
    'eco_id': tf.float32,
    'eco_name': tf.string,
    'grid': tf.string,
    'grid_index': tf.int64
    # 'nb_s1_images': tf.float32
}
```
```python
#
# HELPERS
#
def process_water(parser,element):
  water=parser.image(element,bands=WATER_BANDS,dtype=np.uint8)
  values,counts=np.unique(water,return_counts=True)
  props={v: c for (v,c) in zip(values,counts)}
  props={WATER_COLUMNS[i]: props.get(i,0) for i in range(3)}
  water_ratio=props['water_count']/props['not_water_count']
  props['water_ratio']=water_ratio
  props['valid_water']=((MIN_WATER_RATIO<=water_ratio) and 
            (water_ratio<MAX_WATER_RATIO) and 
            (props['no_data_count']<MAX_WATER_NO_DATA_COUNT))
  return water, props


def process_s1(parser,element):
  s1=parser.image(element,bands=S1_BANDS,dtype=np.float32)
  props={ 
      's1_na_count': np.count_nonzero(np.isnan(s1)),
      's1_zero_count': np.count_nonzero((s1[0]*s1[1])==0),
  }
  props['valid_s1']=((props['s1_na_count']<MAX_S1_NAN_COUNT) and
                     (props['s1_zero_count']<MAX_S1_ZERO_COUNT))
  return s1, props


def image_name(tile_id,year,month):
  name=re.sub('S1','TILE',tile_id)
  return f'{name}_{int(year)}{str(int(month)).zfill(2)}.tif'

```

```python
def run(parser,take=None,skip=0,batch_size=100):
    """ example:
        - parse all data properties (note: you could have also passed `keys` to `.data()` for a subset of properties )
        - parse bands into distinct images
    """
    parsed_data=parser.dataset.skip(skip)
    if take:
      parsed_data=parsed_data.take(take)
    for batch_index, batch in utils.get_batches(parsed_data,batch_size=batch_size):
      print('\n'*2)
      print('='*75)
      print('BATCH:',batch_index)
      print('='*75)
      rows=[]
      for i,element in enumerate(batch):
          if NOISY and (not (i%NOISE_REDUCER)): 
              print(f'\t- {i}...')
          props=parser.data(element)
          water, water_props=process_water(parser,element)
          s1, s1_props=process_s1(parser,element)
          props.update(water_props)
          props.update(s1_props)
          rows.append(props)
          if props['valid_water'] and props['valid_s1']:
              lon=props['lon']
              lat=props['lat']
              crs=props['crs']
              name=image_name(props['tile_id'],props['year'],props['month'])
              utils.image_to_gcs(
                  s1,
                  name,
                  utils.image_profile(lon,lat,crs,RESOLUTION,s1),
                  folder=f'{GCS_FOLDER}/S1',
                  bucket=GCS_BUCKET)
              utils.image_to_gcs(
                  water,
                  name,
                  utils.image_profile(lon,lat,crs,RESOLUTION,water),
                  folder=f'{GCS_FOLDER}/GSW',
                  bucket=GCS_BUCKET)
      df=pd.DataFrame(rows)
      gcs_path=utils.csv_to_gcs(
          df,
          f'EXPORTS_BATCH-{batch_index}.csv',
          folder=f'{GCS_FOLDER}/CSV',
          bucket=GCS_BUCKET)
      print('-'*75)
      print(gcs_path)
```

```
parser=tfp.TFRParser(
    TFR_LIST,
    specs=FEATURE_PROPS,
    band_specs=BANDS,
    dims=[SIZE,SIZE])

run(parser,take=TAKE,skip=SKIP,batch_size=BATCH_SIZE)
```