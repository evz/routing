from flask import Blueprint, make_response, request, render_template
import json
from routing.database import engine
from sqlalchemy import text

api = Blueprint('api', __name__)

@api.route('/')
def index():
    return render_template('index.html')

@api.route('/route/')
def route():
    start = request.args.get('start')
    start_x, start_y = start.split(',')
    end = request.args.get('end')
    end_x, end_y = end.split(',')
    algo = request.args.get('algo', 'dijkstra')
    sel = text(''' 
      SELECT 
        ST_ASGeoJSON(ways.the_geom) 
      FROM ways 
      JOIN (
        SELECT 
          seq, 
          id1 AS node, 
          id2 AS edge_id, 
          cost 
        FROM (
          SELECT id 
            FROM ways_vertices_pgr 
          ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(:start_x, :start_y), 4326) LIMIT 1
        ) AS id1, (
          SELECT 
            id 
          FROM ways_vertices_pgr 
          ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(:end_x, :end_y), 4326) LIMIT 1
        ) AS id2, 
          pgr_dijkstra('SELECT gid AS id, 
                          source::integer, 
                          target::integer, 
                          length::double precision AS cost 
                        FROM ways', 
                        id1.id::int, 
                        id2.id::int, 
                        false, 
                        false)
        ) AS route ON ways.gid = route.edge_id;
    '''.format(algo))
    args = {
        'start_x': start_x,
        'start_y': start_y,
        'end_x': end_x,
        'end_y': end_y
    }
    geo = {
      'type': 'FeatureCollection',
      'features': []
    }
    with engine.begin() as conn:
        rows = list(conn.execute(sel, **args))
    for row in rows:
        d = {'type': 'Feature', 'geometry': json.loads(row[0])}
        geo['features'].append(d)
    resp = make_response(json.dumps(geo))
    resp.headers['content-type'] = 'application/json'
    return resp
