import re
import io
import math
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def is_coordinate(location):
    """
    Check if the given location string is in coordinate format, e.g., "lat,lon".
    """
    pattern = r'^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$'
    return re.match(pattern, location) is not None

def geocode(location):
    # If the location is in coordinate format, parse and return it.
    if is_coordinate(location):
        try:
            lat, lon = map(float, location.split(","))
            return (lat, lon)
        except Exception as e:
            raise Exception(f"Error parsing coordinates: {location}") from e

    # Otherwise, assume it's a place name and call the geocoding API.
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    headers = {
        "User-Agent": "YourAppName/1.0 (contact@yourdomain.com)"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200 or not response.json():
        raise Exception(f"Geocoding API error for place: {location}")
    result = response.json()[0]
    return (float(result["lat"]), float(result["lon"]))

def swap_coordinates(coordinate):
    """
    Given a (lat, lon) tuple, swap it to (lon, lat) as expected by OSRM.
    """
    lat, lon = coordinate
    return f"{lon},{lat}"

def get_route(current_place, pickup_place, dropoff_place):
    """
    Get directions based on real place names.
    """
    current_coords = geocode(current_place)
    pickup_coords = geocode(pickup_place)
    dropoff_coords = geocode(dropoff_place)
    
    current_osrm = swap_coordinates(current_coords)
    pickup_osrm = swap_coordinates(pickup_coords)
    dropoff_osrm = swap_coordinates(dropoff_coords)
    coordinates = f"{current_osrm};{pickup_osrm};{dropoff_osrm}"
    
    url = f"http://router.project-osrm.org/route/v1/driving/{coordinates}"
    params = {"overview": "full", "geometries": "geojson", "steps": "true"}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"OSRM API Error: {response.text}")
    data = response.json()
    if "routes" not in data or not data["routes"]:
        raise Exception("No route data received from OSRM API")
    
    route = data["routes"][0]
    distance_miles = route["distance"] * 0.000621371
    duration_hours = route["duration"] / 3600
    legs = route.get("legs", [])
    
    formatted_instructions = []
    for i, leg in enumerate(legs):
        if i == 0:
            start_place, end_place = current_place, pickup_place
        else:
            start_place, end_place = pickup_place, dropoff_place

        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            step_type = maneuver.get("type", "")
            modifier = maneuver.get("modifier", "")
            road_name = step.get("name", "")
            step_distance = round(step.get("distance", 0) * 0.000621371, 2)
            if step_type == "depart":
                instruction_str = f"Depart from {start_place} onto {road_name} and continue for {step_distance} miles."
            elif step_type == "arrive":
                instruction_str = f"Arrive at {end_place}."
            else:
                if modifier:
                    instruction_str = f"{step_type.capitalize()} {modifier} onto {road_name} and continue for {step_distance} miles."
                else:
                    instruction_str = f"{step_type.capitalize()} onto {road_name} and continue for {step_distance} miles."
            formatted_instructions.append(instruction_str)
    
    map_url = (
        f"https://www.openstreetmap.org/directions?engine=osrm_car"
        f"&route={current_osrm};{pickup_osrm};{dropoff_osrm}"
    )
    
    return {
        "distance": distance_miles,
        "duration": duration_hours,
        "instructions": formatted_instructions,
        "map_url": map_url,
        "geometry": route.get("geometry")
    }

def generate_daily_logs(trip, route_data):
    """
    Generate daily logs combining route data and trip details.
    Additionally, create a status grid timeline for each day reflecting:
      0: Off Duty, 1: Sleeper Berth, 2: Driving, 3: Break, 4: On Duty.
    This version allocates driving hours up to 11 per day until the total driving time is exhausted.
    If driving in a day exceeds 8 hours, a 30-minute break (simulated as one hour on the grid) is inserted.
    """
    # Total driving time in hours (from OSRM route)
    total_driving = route_data.get("duration", 0)
    # Total distance in miles
    total_distance = route_data.get("distance", 0)
    
    # Fixed stops (pickup + dropoff) and fueling stops add to overall on-duty time.
    fixed_stops_time = 2  # hours
    fueling_stop_time = (total_distance // 1000) * 0.5  # hours
    adjusted_duration = total_driving + fixed_stops_time + fueling_stop_time

    # For FMCSA, a driver can drive up to 11 hours in a day.
    max_daily_driving = 11
    # We assume an 8-day cycle as per FMCSA’s 70-hour limit.
    cycle_days = 8

    # Allocate driving hours per day (greedy allocation up to 11 hours per day)
    daily_driving_alloc = []
    remaining_driving = total_driving
    for day in range(cycle_days):
        if remaining_driving <= 0:
            daily_driving_alloc.append(0)
        else:
            day_driving = min(max_daily_driving, remaining_driving)
            daily_driving_alloc.append(day_driving)
            remaining_driving -= day_driving

    logs = []
    # For each day in the cycle, create a timeline.
    for day in range(1, cycle_days + 1):
        day_driving = daily_driving_alloc[day - 1]
        # Calculate daily distance proportionally.
        daily_distance = total_distance * (day_driving / total_driving) if total_driving > 0 else 0

        # Build a 24-hour timeline.
        # We assume the day starts at 0:00 but the driving window starts at 6:00.
        timeline = [0] * 24  # default Off Duty (status 0)
        start_hour = 6
        # End hour based on day_driving (could be fractional)
        end_hour = start_hour + day_driving

        if day_driving <= 8:
            # All driving is continuous.
            for hr in range(start_hour, min(24, int(round(end_hour)))):
                timeline[hr] = 2  # Driving.
        else:
            # First 8 hours are driving.
            for hr in range(start_hour, min(24, 6 + 8)):
                timeline[hr] = 2
            # Insert a break after 8 hours.
            if 14 < 24:
                timeline[14] = 3  # Break (simulated as a full hour for the grid)
            # Resume driving starting at hour 15.
            remaining_hours = day_driving - 8
            rem_full = int(round(remaining_hours))
            for hr in range(15, min(24, 15 + rem_full)):
                timeline[hr] = 2

        # Build a 5-row status grid (rows 0 to 4 for statuses Off Duty, Sleeper Berth, Driving, Break, On Duty).
        numRows = 5
        statusGrid = [ [None]*24 for _ in range(numRows)]
        for hr in range(24):
            st = timeline[hr]
            # Only set the cell for the appropriate status.
            statusGrid[st][hr] = st

        # For reporting, if a break was inserted, count it as 0.5 hour extra.
        break_time = 0.5 if day_driving > 8 else 0
        effective_driving_hours = day_driving + break_time
        rest_hours = max(0, 24 - effective_driving_hours)
        
        log_entry = {
            "cycle": 1,  # For simplicity, assume one cycle.
            "day": day,
            "driver_name": trip.driver.username if trip.driver else "",
            "carrier": trip.driver.carrier if trip.driver else "",
            "truck_number": trip.driver.truck_number if trip.driver else "",
            "home_terminal_address": trip.driver.home_terminal_address if trip.driver else "",
            "shipping_docs": trip.driver.shipping_docs if trip.driver else "",
            "driver_signature": trip.driver.driver_signature if trip.driver else "",
            "current_cycle_hours": getattr(trip, "current_cycle_hours", ""),
            "current_location": trip.current_location,
            "pickup_location": trip.pickup_location,
            "dropoff_location": trip.dropoff_location,
            "daily_distance": round(daily_distance, 2),
            "daily_driving_hours": round(day_driving, 2),
            "break_time": break_time,
            "effective_driving_hours": round(effective_driving_hours, 2),
            "rest_hours": round(rest_hours, 2),
            "fueling_stop": False, 
            "pickup": (day == 1),
            "dropoff": (day == cycle_days),
            "remarks": (
                f"Day {day}: {trip.driver.username if trip.driver else 'N/A'} driving from "
                f"{trip.current_location} to {trip.dropoff_location} via {trip.pickup_location}"
            ),
            "date": trip.created_at,
            "onDutyHours": round(effective_driving_hours, 2),
            "seventyHrEightDay": 70,
            "sixtyHrSevenDay": 60,
            "statusGrid": statusGrid
        }
        logs.append(log_entry)
    return logs
