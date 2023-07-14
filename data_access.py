import sqlite3;
import json;

from werkzeug.security import check_password_hash

class User:
    def __init__(self, id,  email, password, name, auth = False, ) -> None:
        self.id = email
        self.password = password
        self.auth = auth
        self.name = name
        self.dbid = id

    def is_authenticated(self):
        return self.auth
    
    def is_active():
        return True
    
    def get_id(self):
        return self.id
    

class SQLiteConnection:
    def __init__(self, path,
                 default_user:User) -> None:
        self.test_user = default_user
        self.con = sqlite3.connect(path, check_same_thread=False)
        print("\t** Db connected")
        self._createTables(default_user)
    
    
    def _createTables(self, def_user:User)-> None :
        cursor = self.con.cursor()

        #Creating Vehicle Table
        create_vehicle_table_sql = """
            CREATE TABLE IF NOT EXISTS Vehicle(
                id TEXT PRIMARY KEY     NOT NULL,
                plate   TEXT UNIQUE     NOT NULL,
                driver_name TEXT        NOT NULL,
                model   TEXT            NOT NULL,
                type    TEXT            
            )
        """
        cursor.execute(create_vehicle_table_sql)
        print("\t** Created Table Vehicle")

        # Creating VehiclePosition Table to store vehicle positions
        create_VehiclePos_table_sql = """
            CREATE TABLE IF NOT EXISTS VehiclePosition(
                id TEXT PRIMARY KEY     NOT NULL,
                lat TEXT                NOT NULL, 
                lng TEXT                NOT NULL
            );
        """

        cursor.execute(create_VehiclePos_table_sql)
        print("\t** Created Table VehiclePositions")

        #Populating test data for Vehicles Table
        f = open(".\\db\\test_vehicle_data.json", 'r');
        d = json.load(f)
        
        # Bulk insert to VehiclePostition or Ignore if exists.
        cursor.executemany('INSERT OR IGNORE INTO VehiclePosition (id, lat, lng)'
                           ' VALUES (:id, :lat, :lng)', d['vehicle_positions'])
        cursor.executemany('INSERT OR IGNORE INTO Vehicle (id, plate, driver_name, model, type) '
                           ' VALUES (:id, :plate, :driver_name, :model, :type)', d["vehicles"])
        

        #Creating User Table
        create_user_table_sql = """
            CREATE TABLE IF NOT EXISTS User(
                id          INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                email       UNIQUE,
                name        TEXT NOT NULL,
                password    TEXT NOT NULL
            )
        """

        cursor.execute(create_user_table_sql);

        cursor.execute('''INSERT OR IGNORE INTO User(email, name, password) 
                        VALUES ('{0}', '{1}', '{2}') '''.format(def_user.id, 
                                                              def_user.name, 
                                                              def_user.password))
        print("\t** Created Table User")
        
        #Creating Bookings Table
        create_Booking_table_sql = """
            CREATE TABLE IF NOT EXISTS Booking(
                id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                vehicle_id     TEXT,
                start_x         TEXT NOT NULL,
                start_y         TEXT NOT NULL,
                end_x           TEXT NOT NULL,
                end_y           TEXT NOT NULL,
                path            TEXT, 
                currentPos      TEXT,
                lastIdxOfPath   INTEGER DEFAULT 0,
                user_id         INTEGER,
                started         BOOLEAN DEFAULT 0,
                ended           BOOLEAN DEFAULT 0,
                rating          INTEGER DEFAULT 0,
                start_time      TIMESTAMP DEFAULT (DATETIME('now')),
                end_time      TIMESTAMP DEFAULT (DATETIME('now')),
                FOREIGN KEY(user_id) REFERENCES User(id)
            )
        """
        cursor.execute(create_Booking_table_sql);
        print("\t** Created Table Booking")

        self.con.commit()
        cursor.close()
    
    # For Executing sql via connection
    def _read(self, sql) -> sqlite3.Cursor:
        return self.con.execute(sql);

    # Method for formating sql rows.
    def _dict_factory(self, cursor:sqlite3.Cursor, row) -> dict:
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    # Get Data from table VehiclePositions
    def getAllVehicles(self, exludeBooked = False, type : str = None) -> dict:
        sql = 'select vp.*, v.type from VehiclePosition vp join Vehicle v on vp.id=v.id'
        cond = ""
        if exludeBooked:
            cond += " vp.id not in (SELECT vehicle_id from Booking WHERE NOT(started AND ended))"
        if type is not None and isinstance(type, str):
            cond += " and v.type='{0}'".format(type)

        if (exludeBooked or type is not None):
            sql += ' WHERE ' + cond
        cursor = self._read(sql=sql)
        cursor.row_factory = self._dict_factory;
        data = cursor.fetchall()
        cursor.close()
        return data;

    # Get vehicle details for an vehicle id
    def getVehicleDetails(self, id):
        # sql = 'SELECT * FROM VehiclePosition vp JOIN Vehicle v on vp.id=v.id WHERE vp.id=\'{0}\''.format(id)
        
        sql = '''SELECT vp.*, v.*, avg(b.rating) as avg_rating 
                FROM VehiclePosition vp 
                JOIN Vehicle v on vp.id=v.id 
                LEFT JOIN booking b on vp.id=b.vehicle_id 
                WHERE vp.id='{0}' GROUP BY v.id'''.format(id)
        
        cursor = self.con.cursor()
        cursor.row_factory = self._dict_factory
        cursor.execute(sql);
        data = cursor.fetchone()
        cursor.close()
        return data
    

    def book(self, vehicleId, start_x, start_y, end_x, end_y, user, pathString=None):
        sql = '''INSERT INTO Booking(vehicle_id, start_x, start_y, end_x, end_y, path, user_id) 
                VALUES('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')
                '''.format(vehicleId, start_x, start_y, end_x, end_y, pathString, user)
        cursor = self.con.cursor();
        cursor.execute(sql);
        self.con.commit();
        cursor.close();

    def resetDataState(self):
        self.con.execute('DELETE FROM Booking')
        self.con.execute('DELETE FROM VehiclePosition')
        self._createTables(self.test_user);
    
    def getOnGoingBooking(self, id=None):
        sql = "SELECT * FROM Booking"
        if id is not None:
            sql += " WHERE id={0}".format(id)
        else:
            sql += " WHERE NOT(started AND ended)"
        cursor = self._read(sql);
        cursor.row_factory = self._dict_factory;
        data = cursor.fetchall()
        cursor.close()
        return data;

    def getBookingForUser(self, u_id):
        # sql = '''SELECT b.id as 'b_id', b.vehicle_id, start_x, start_y, end_x, b.started, b.ended, end_y, v.*
        #          FROM Booking b JOIN Vehicle v ON b.vehicle_id=v.id  WHERE user_id = {0}
        #           AND b.ended = 0 '''.format(u_id)
        sql = '''SELECT b.id as 'b_id', b.vehicle_id, start_x, start_y, end_x, b.started, b.ended, end_y
                 FROM Booking b  WHERE user_id = {0}
                  AND b.ended = 0 '''.format(u_id)
        print(sql);
        cursor = self._read(sql);
        cursor.row_factory = self._dict_factory
        data = cursor.fetchone()
        cursor.close()

        if(data is not None and 'vehicle_id' in data):
            v_data = self.getVehicleDetails(data['vehicle_id']);
            return {**data, **v_data}
        else:
            return {}
    
    def startJourneyForUser(self, u_id):
        booking = self.getBookingForUser(u_id)
        sql = '''UPDATE Booking 
                SET started=1, start_time=DATETIME('now') 
                WHERE id = '{0}' AND ended=0 '''.format(booking['b_id'])
        cursor = self.con.cursor();
        cursor.execute(sql);
        self.con.commit()
        cursor.close();
    
    def endJourneyForUser(self, u_id):
        booking = self.getBookingForUser(u_id)
        sql = '''UPDATE Booking 
                SET ended=1, end_time=DATETIME('now')
                WHERE id = '{0}' AND started=1 '''.format(booking['b_id'])
        cursor = self.con.cursor();
        cursor.execute(sql);
        self.con.commit()
        cursor.close();
    
    def rateBooking(self, u_id, rating):
        sql1 = "SELECT id from Booking WHERE user_id='{0}' ORDER BY end_time DESC LIMIT 1".format(u_id)
        booking = self.con.execute(sql1).fetchone();
        sql = "UPDATE Booking SET rating={1} WHERE id='{0}'".format(booking[0], rating)
        print(sql)
        cursor = self.con.cursor()
        cursor.execute(sql)
        self.con.commit()
        cursor.close()
     

    def updateBookedVehiclePos(self, booking_id:int, lat, lng, lastIdxOfPath=0):
        pos = "({0}, {1})".format(lat, lng);

        sql = '''UPDATE Booking SET currentPos='{0}', lastIdxOfPath='{1}' 
                    WHERE id='{2}' '''.format(pos, lastIdxOfPath, booking_id)
        
        cursor = self.con.cursor()

        cursor.execute(sql)
        self.con.commit()

    def updateVehiclePosition(self, vehicle_id, lat, lng):
        sql2 = '''UPDATE VehiclePosition SET lat='{0}', lng='{1}' WHERE id='{2}'  '''.format(lat, lng, vehicle_id)
        cursor = self.con.cursor()
        cursor.execute(sql2)
        self.con.commit()
        cursor.close();
    
    def getPreviousJourneys(self, u_id):
        sql = '''SELECT b.id, v.plate, v.driver_name, v.type, start_time, end_time, rating 
                 FROM booking b JOIN vehicle v ON v.id=b.vehicle_id 
                 WHERE b.ended and b.user_id={0}'''.format(u_id)
        cursor = self.con.cursor()
        cursor.row_factory = self._dict_factory
        cursor.execute(sql);
        data = cursor.fetchall();
        cursor.close();
        return data;
       

    def getUser(self, email, pw=""):
        sql = "SELECT * FROM User Where email='{0}'".format(email)
        cursor = self.con.cursor()
        cursor.row_factory = self._dict_factory
        cursor.execute(sql)
        data = cursor.fetchone()
        cursor.close()

        if(data is None):
            return None

        # auth = pw_hash==data['password']
        auth = check_password_hash(data['password'], pw)
        return User(data['id'],email, data['password'], data['name'], auth)
    
                

#Testing
if __name__ == '__main__':
    print(":::SQLiteConnection tests")
    con = SQLiteConnection('.\\test.sqlite3');
    v_pos = con.getAllVehicles();

    for i in v_pos:
        print(i)


    

