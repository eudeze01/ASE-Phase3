from flask import (Flask, render_template, jsonify, request, redirect, url_for, flash, make_response)
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
import json
import os
import re

from db.data_access import SQLiteConnection, User
from BusinessLayer.notuber import NotUber
from utilities import move1DistanceUnitAlong

# User for testing
test_user = User("john@abc.com",generate_password_hash("1234"), "John Smith")

#Creates SQLiteConnection object to access database
db = SQLiteConnection(".\\db\\notuberdb.sqlite3", test_user);
#Create Business Logic Layer
bl = NotUber();

app = Flask(__name__, static_url_path='', 
            static_folder='web/static', 
            template_folder='web/template');

app.secret_key = "u3JDCKb7czuQ9Y556Dvz9PDgndLDEdNP"

#Setting up for Login
login_manger = LoginManager(app=app)
login_manger.login_view = 'login'

@login_manger.user_loader
def load_user(user_id):
    return db.getUser(user_id, "")

#Login Route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if(request.method=='POST'):

        user_id = request.form["username"]
        pw = request.form["password"]

        user = db.getUser(user_id, pw)
        
        if(user is not None and user.is_authenticated()):
            login_user(user)
            next = request.args.get('next')

            return redirect(next or url_for('index'))
        else:
            flash("User Name/Password Wrong.")

    return render_template('login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# Main Route for serving html template
@app.route("/")
@login_required
def index():
    resp = make_response(render_template("index.html", name=current_user))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp;

# API Route for serve vehicle positions
@app.route("/getVehicles")
def getVehicles():
    vehicles = db.getAllVehicles()
    return jsonify(vehicles)

@app.route("/api/getVehicleDetails", methods=['GET'])
def getVehicleDetails():
    _id = request.args['id']
    vehicle = db.getVehicleDetails(_id)

    return jsonify(vehicle)

#API Route for book vehicle
@app.route("/api/book", methods=['post'])
def book():

    flaskReq_params = request.get_json();

    if 'source' not in flaskReq_params or 'x' not in flaskReq_params['source'] or 'y' not in flaskReq_params['source']:
        raise BadRequest("Request body doesn't have 'source':\{'x':lat, 'y':lng\} properly defined")

    freeVechicles = db.getAllVehicles(True);
    if len(freeVechicles)==0:
        return jsonify({})
    
    closest = bl.getClosestVehicle(
        {'x':flaskReq_params['source']['x'], 'y':flaskReq_params['source']['y']},
        freeVechicles)
    
    # print(flaskReq_params['pathArray']);
    
    if 'car_id' in closest:
        db.book(closest['car_id'], flaskReq_params['source']['x'],
                flaskReq_params['source']['y'], 
                flaskReq_params['destination']['x'],
                flaskReq_params['destination']['y'],
                flaskReq_params['pathArray'])
    
    return jsonify(closest)


@app.route("/api/tick")
def tick():
    # TODO : 
    # 1. Get Booked Vehicles
    # 2. foreach get polyline for journey
    # 3.  get last point and fraction
    # 4. calculate,interpolated 
    #

    distance_unit = 1 #in kilometers

    booked = db.getBookedVehicles()
    for rec in booked:
        # print(rec['path'])
        regex = r'''\((?P<lat>[\+\-]?\d+\.\d+)\,\s*(?P<lng>[\+\-]?\d+\.\d+)\)'''
        matcher = re.compile(regex);
        positionArr = [m.groupdict() for m in matcher.finditer(rec['path'])]
        # print(poitionArr)

        if(rec['currentPos'] is None):
            db.updateBookedVehiclePos(rec['id'], positionArr[0].get('lat'),
                                      positionArr[0].get('lng'))
        else:

            print("came to move car")
            a = [float(i) for i in str(rec['currentPos'])[1:][:-1].split(',')]

            b = move1DistanceUnitAlong(positionArr, {'lat':a[0], 'lng':a[1]}, rec['lastIdxOfPath'])
            db.updateBookedVehiclePos(rec['id'], b[0]['lat'], b[0]['lng'],b[1])
            db.updateVehiclePosition(rec['vehicle_id'], b[0]['lat'], b[0]['lng'])

    vehicle_positions = db.getAllVehicles();

    return jsonify(vehicle_positions)

@app.route("/api/reset", methods=['get'])
def reset():
    db.resetDataState();
    vehicles = db.getAllVehicles()
    return jsonify(vehicles)

@app.route("/api/status", methods=['get'])
def status():
    vehicles = db.getAllVehicles()
    return jsonify(vehicles)

@app.route("/api/getBingKey", methods=['get'])
def bingApiKey():
    return jsonify({'key':os.environ['BING_MAPS_API_KEY']})

#Error Handling
@app.errorhandler(404)
def not_found_error(e):
    response = e.get_response()

    response.data = json.dumps({'error':{
        "code": e.code,
        "name": e.name,
        "description": e.description,
    }})
    response.content_type = "application/json"
    return response

@app.errorhandler(BadRequest)
def bad_request_error(e):
    print(e);
    response = e.get_response()

    response.data = json.dumps({'error':{
        "code": e.code,
        "name": e.name,
        "description": e.description,
    }})
    response.content_type = "application/json"
    return response


