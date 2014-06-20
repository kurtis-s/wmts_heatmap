import config
from flask import Flask, json
import psycopg2
app = Flask(__name__)

USAGE_QUERY='''SELECT astext(ST_SnapToGrid(ST_Centroid(ST_Transform(request_bbox, 3857)), (20037508.342789244*2)/20, (20037508.342789244*2)/20)), count(*)
FROM analytics an, request_parameter rp
WHERE an.id = rp.analytics_id
AND an.service_type='Earth Service:WMTS'
AND an.request_bbox is not null
AND an.create_date > NOW() - '1 hours'::INTERVAL
AND rp.name='TileMatrixSet'
AND rp.value='EPSG:3857'
GROUP BY ST_SnapToGrid(ST_Centroid(ST_Transform(request_bbox, 3857)), (20037508.342789244*2)/20, (20037508.342789244*2)/20);
'''

def query_db():
    conn_string = "host={host} port={db_port} dbname={db_name} user={db_user} password={db_password}".format(
                      host=config.DB_HOST,
                      db_port=config.DB_PORT,
                      db_name=config.DB_NAME,
                      db_user=config.DB_USERNAME,
                      db_password=config.DB_PASSWORD)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute(USAGE_QUERY)
    records = cursor.fetchall()
    return records

def parse_usage_query(record):
    count = record[1]
    coordinate_string = str.rstrip(str.lstrip( record[0], 'POINT(' ), ')')
    longitude, latitude = coordinate_string.split()
    return count, longitude, latitude

def usage_stats():
    points = [] 
    records = query_db()
    for rec in records:
        count, longitude, latitude = parse_usage_query(rec) 
        points.append({'point':{'longitude': longitude,
                                'latitude': latitude,
                                'count': count}})
    return {'points': points}

@app.route('/')
def usage_stats_by_region():
    return json.dumps(usage_stats())

if __name__=='__main__':
    app.debug = True
    app.run()
