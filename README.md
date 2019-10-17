### TFR2Human

_easy parsing of TFRecords_

---

#### INSTALL

```bash
git clone https://github.com/brookisme/tfr2human.git
pip install -e tfr2human
```

---

#### BASIC EXAMPLE

```
INPUT_BANDS=['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11', 'B12']
RGB_BANDS=['red','green','blue']
WATER_BANDS=['water']
S1_BANDS=['VV','VH','angle']
CLOUD_BANDS=['cirrus','opaque']
BANDS=INPUT_BANDS+RGB_BANDS+CLOUD_BANDS+WATER_BANDS+S1_BANDS

FEATURE_PROPS={
    'tile_id': tf.string,
    'crs': tf.string,
    'year': tf.float32,
    'month': tf.float32,
    'surface_water_date': tf.string,
    'lon': tf.float32,
    'lat': tf.float32,
    'x_offset': tf.float32,
    'y_offset': tf.float32,
    'input_date': tf.string,
    'water_frac': tf.float32,
    'black_frac': tf.float32,
    'opaque_frac': tf.float32,
    'cirrus_frac': tf.float32,
    'nan_frac': tf.float32
}

def run(parser,take=2,skip=0):
    """ example:
        - parse all data properties (note: you could have also passed `keys` to `.data()` for a subset of properties )
        - parse bands into distinct images
    """
    rows=[]
    for i,element in enumerate(parser.dataset.skip(skip).take(take)):
        if NOISY and (not (i%NOISE_REDUCER)): 
            print(i,'...')
        props=parser.data(element)
        print('PROPERTIES:')
        pprint(props)
        print()
        inpt=parser.image(element,bands=INPUT_BANDS,dtype=np.uint16)
        rgb=parser.image(element,bands=RGB_BANDS,dtype=np.uint8)
        water=parser.image(element,bands=WATER_BANDS,dtype=np.uint8)
        s1=parser.image(element,bands=S1_BANDS,dtype=np.float32)
        print('SENTINEL-1:',s1.shape,s1.max(),s1.min())
        print('SENTINEL-2:',inpt.shape,inpt.max(),inpt.min())
        print('RGB:',rgb.shape,rgb.max(),rgb.min())
        print('TARGET:',water.shape,water.max(),water.min())


parser=TFRParser(
    TFR_LIST,
    specs=FEATURE_PROPS,
    band_specs=BANDS,
    dims=[384,384])

run(parser,take=1,skip=0)

"""ouptut

PROPERTIES:
{'black_frac': 0.0,
 'cirrus_frac': 0.4398,
 'crs': 'EPSG:32736',
 'input_date': '2018-01-19',
 'lat': -13.60786,
 'lon': 34.578312,
 'month': 1.0,
 'nan_frac': 0.072,
 'opaque_frac': 0.5502,
 'surface_water_date': '2018-01-01',
 'tile_id': 'S2_34.578311242442226_-13.607859586899323',
 'water_frac': 0.9267,
 'x_offset': -58.0,
 'y_offset': -54.0,
 'year': 2018.0}

SENTINEL-1: (3, 384, 384) 39.162453 0.0
SENTINEL-2: (12, 384, 384) 4184 329
RGB: (3, 384, 384) 255 103
TARGET: (1, 384, 384) 2 0

"""
```