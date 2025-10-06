import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# NASA API Key
NASA_API_KEY = "Xsfl9OgXhhp1Wmd3LrF7hzgFLRclZhA6R7Thb1cX"

# CelesTrak provides official NASA/USSPACECOM TLE data
# This is the authoritative source for satellite orbital elements
CELESTRAK_GROUPS = {
    "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
    "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",  # Includes ISS
    "geo": "https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle",
    "active": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
    "nasa": "https://celestrak.org/NORAD/elements/gp.php?GROUP=nasa&FORMAT=tle"  # NASA satellites only
}

def fetch_tles(group="active", limit=100):
    """Fetch TLEs from CelesTrak with group filtering"""
    url = CELESTRAK_GROUPS.get(group, CELESTRAK_GROUPS["active"])
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        sats = []
        
        # TLEs are 3 lines: name, line1, line2
        for i in range(0, min(len(lines), limit * 3), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                tle1 = lines[i + 1].strip()
                tle2 = lines[i + 2].strip()
                
                # Extract orbit type from mean motion (revs per day)
                try:
                    mean_motion = float(tle2[52:63])
                    if mean_motion > 11.0:
                        orbit_type = "LEO"
                        color = "#00ff88"
                    elif mean_motion > 1.5:
                        orbit_type = "MEO"
                        color = "#ffaa00"
                    else:
                        orbit_type = "GEO"
                        color = "#ff3366"
                except:
                    orbit_type = "UNKNOWN"
                    color = "#888888"
                
                sats.append({
                    "name": name,
                    "tle1": tle1,
                    "tle2": tle2,
                    "orbit_type": orbit_type,
                    "color": color
                })
        
        return sats
    except Exception as e:
        print(f"Error fetching TLEs: {e}")
        return []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/satellites")
def satellites():
    """Return all satellites with metadata"""
    leo_sats = fetch_tles("active", limit=60)
    geo_sats = fetch_tles("geo", limit=20)
    stations = fetch_tles("stations", limit=5)
    starlink = fetch_tles("starlink", limit=30)
    
    all_sats = leo_sats + geo_sats + stations + starlink
    
    # Remove duplicates by name
    seen = set()
    unique_sats = []
    for sat in all_sats:
        if sat["name"] not in seen:
            seen.add(sat["name"])
            unique_sats.append(sat)
    
    return jsonify({
        "satellites": unique_sats[:50],
        "count": len(unique_sats[:50]),
        "timestamp": requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC").json()["datetime"] 
                     if True else None
    })

@app.route("/api/stats")
def stats():
    """Return satellite statistics"""
    sats = fetch_tles("active", limit=100)
    leo = sum(1 for s in sats if s["orbit_type"] == "LEO")
    meo = sum(1 for s in sats if s["orbit_type"] == "MEO")
    geo = sum(1 for s in sats if s["orbit_type"] == "GEO")
    
    return jsonify({
        "total": len(sats),
        "leo": leo,
        "meo": meo,
        "geo": geo
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)