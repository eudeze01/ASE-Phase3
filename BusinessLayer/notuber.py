import os
import requests

class NotUber:
    def __init__(self) -> None:
        pass

    def getClosestVehicle(self, startPoint, vehiclePositions):
        mapUrl = "https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix"
        # origins=7.270712, 80.605008;7.261162, 80.592606&destinations=7.291454, 80.635567&travelMode=driving&key=As_aChto7Tgx9cRvOVYr8hAvyUVnU3DuMjb4VEHXHCpf0aDGH0F5vhpEHMGK4HTl
        urlParams = {'origins' : ';'.join(i['lat']+","+i['lng'] for i in vehiclePositions), 
                    'destinations': '{0}, {1}'.format(startPoint['x'], startPoint['y']),
                    'travelMode' : "driving",
                    'key' : os.environ['BING_MAPS_API_KEY']}

        paramsStr = "&".join("%s=%s" % (k,v) for k,v in urlParams.items())
        # print(paramsStr)

        # return jsonify(request.get_json());
        apiRes = requests.get(mapUrl, params=paramsStr);
        if apiRes.ok:
            a = apiRes.json();
            route_matrix = a['resourceSets'][0]['resources'][0]['results']
            # print(json.dumps(extract, indent=3))
            least = min(route_matrix, key=lambda x: x['travelDistance'])
        
            min_distance_idx = least['originIndex']
            time = least['travelDuration']

            if min_distance_idx < len(vehiclePositions):
                r = {'car_id':vehiclePositions[min_distance_idx]['id'], 
                    'total_time': time,
                    'total_distance' : least['travelDistance']}
                return r
            else:
                return {}
        else:
            raise Exception({'message' : "Call to bing distace matrix failed",
                             'url': apiRes.url})
        
