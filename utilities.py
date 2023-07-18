import math

def distace_between(lat1:float, lng1:float, lat2:float, lng2:float):
    R = 6371  # Radius of the Earth in kilometers
    # Convert latitude and longitude to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # Calculate the difference between the two coordinates
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    # Calculate the haversine of half the differences
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2

    # Calculate the great circle distance in radians
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance in kilometers
    return R*c

# Method to find coordinate of a point which is 
# T kilometers away from point 1 towards point 2
def find_coordinates(lat1, lon1, lat2, lon2, T):
    R = 6371  # Radius of the Earth in kilometers

    # Convert latitude and longitude to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate the difference between the two coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Calculate the haversine of half the differences
    # a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2

    
    # Calculate the bearing from the first point to the second point
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    bearing = math.atan2(y, x)

    # Calculate the new coordinates T kilometers away in the direction of the bearing
    new_lat = math.asin(math.sin(lat1_rad) * math.cos(T / R) + math.cos(lat1_rad) * math.sin(T / R) * math.cos(bearing))
    new_lon = lon1_rad + math.atan2(math.sin(bearing) * math.sin(T / R) * math.cos(lat1_rad),
                                    math.cos(T / R) - math.sin(lat1_rad) * math.sin(new_lat))

    # Convert the new latitude and longitude back to degrees
    new_lat_deg = math.degrees(new_lat)
    new_lon_deg = math.degrees(new_lon)

    return {'lat':new_lat_deg, 'lng':new_lon_deg}

def move1DistanceUnitAlong(path:list, currentPosition, lastcheckpoint):
    if(len(path)-2 > lastcheckpoint and lastcheckpoint>=0):
        
        d=0
        candidate_last_cp = -1
        next_coordinates = None

        for i in range(lastcheckpoint, len(path)-2):
            d_i = 0
            if i==lastcheckpoint:
                d_i += distace_between(currentPosition['lat'], currentPosition['lng'], 
                                     float(path[i+1]['lat']), float(path[i+1]['lng']))
            else:
                d_i= distace_between(float(path[i]['lat']), float(path[i]['lng']), 
                                    float(path[i+1]['lat']), float(path[i+1]['lng']))
            
            if d+d_i>1:  #1 in here is the unit distance. i.e. 1Km
                candidate_last_cp = i
                if(candidate_last_cp == lastcheckpoint):
                    next_coordinates = find_coordinates(currentPosition['lat'], currentPosition['lng'],
                                 float(path[i+1]['lat']), float(path[i+1]['lng']), 1)
                else:
                    v = 1-d
                    next_coordinates = find_coordinates(float(path[i]['lat']), float(path[i]['lng']),
                                 float(path[i+1]['lat']), float(path[i+1]['lng']), v)
                break
            else:
                d += d_i

        return next_coordinates, candidate_last_cp
    else:
        return path[len(path)-1], len(path)-1


if __name__ == '__main__':
    # a = find_coordinates(51.540841, -0.076502, 51.542355, -0.07628, 0.1)
    a = distace_between(51.540841, -0.076502, 51.542355, -0.07628)
    print(a)
