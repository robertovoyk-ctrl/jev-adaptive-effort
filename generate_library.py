#!/usr/bin/env python3
"""Generate a realistic 8-year iTunes/Apple Music listening history CSV."""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# Real artists and tracks grouped by genre/era feel
LIBRARY = {
    "Radiohead": {
        "genre": "Alternative Rock",
        "tracks": ["Creep", "Karma Police", "No Surprises", "Everything In Its Right Place",
                    "Idioteque", "Paranoid Android", "Lucky", "Exit Music (For a Film)",
                    "How to Disappear Completely", "There There", "15 Step", "Reckoner",
                    "Lotus Flower", "Bloom", "Burn the Witch", "Daydreaming"]
    },
    "Kendrick Lamar": {
        "genre": "Hip-Hop",
        "tracks": ["HUMBLE.", "DNA.", "Alright", "King Kunta", "Swimming Pools",
                    "Money Trees", "m.A.A.d city", "Poetic Justice", "LOVE.",
                    "ELEMENT.", "LOYALTY.", "United in Grief", "Die Hard", "N95",
                    "Rich Spirit", "Not Like Us", "Euphoria"]
    },
    "Tame Impala": {
        "genre": "Psychedelic Pop",
        "tracks": ["The Less I Know the Better", "Let It Happen", "Feels Like We Only Go Backwards",
                    "Elephant", "New Person, Same Old Mistakes", "Borderline",
                    "Lost in Yesterday", "Is It True", "Breathe Deeper", "One More Year"]
    },
    "Arctic Monkeys": {
        "genre": "Indie Rock",
        "tracks": ["Do I Wanna Know?", "R U Mine?", "505", "Fluorescent Adolescent",
                    "I Bet You Look Good on the Dancefloor", "When the Sun Goes Down",
                    "Crying Lightning", "Cornerstone", "Why'd You Only Call Me When You're High?",
                    "Four Out of Five", "Tranquility Base Hotel + Casino", "Body Paint",
                    "There'd Better Be a Mirrorball", "Sculptures of Anything Goes"]
    },
    "Frank Ocean": {
        "genre": "R&B",
        "tracks": ["Thinkin Bout You", "Nights", "Pink + White", "Self Control",
                    "Ivy", "Pyramids", "Swim Good", "Novacane", "Lost",
                    "Chanel", "Nikes", "Solo", "White Ferrari", "Godspeed"]
    },
    "Daft Punk": {
        "genre": "Electronic",
        "tracks": ["Get Lucky", "Around the World", "One More Time", "Harder Better Faster Stronger",
                    "Instant Crush", "Lose Yourself to Dance", "Something About Us",
                    "Digital Love", "Veridis Quo", "Giorgio by Moroder", "Touch",
                    "Within", "Beyond", "Give Life Back to Music"]
    },
    "The Weeknd": {
        "genre": "R&B/Pop",
        "tracks": ["Blinding Lights", "Starboy", "The Hills", "Can't Feel My Face",
                    "Save Your Tears", "After Hours", "Heartless", "In Your Eyes",
                    "Call Out My Name", "I Feel It Coming", "Die For You",
                    "Take My Breath", "Sacrifice", "Less Than Zero", "Popular"]
    },
    "Mac DeMarco": {
        "genre": "Indie Pop",
        "tracks": ["Chamber of Reflection", "My Old Man", "Salad Days", "Freaking Out the Neighborhood",
                    "Let My Baby Stay", "Still Beating", "On the Level", "This Old Dog",
                    "Nobody", "All of Our Yesterdays", "Heart to Heart"]
    },
    "Tyler, The Creator": {
        "genre": "Hip-Hop",
        "tracks": ["See You Again", "EARFQUAKE", "NEW MAGIC WAND", "A BOY IS A GUN*",
                    "IFHY", "Answer", "Yonkers", "She", "Tamale",
                    "LUMBERJACK", "WUSYANAME", "SWEET / I THOUGHT YOU WANTED TO DANCE",
                    "SORRY NOT SORRY", "DOGTOOTH", "Noid", "St. Chroma"]
    },
    "Bon Iver": {
        "genre": "Indie Folk",
        "tracks": ["Skinny Love", "Holocene", "Re: Stacks", "Flume",
                    "Perth", "Towers", "Calgary", "22 (OVER S∞∞N)",
                    "8 (circle)", "Hey, Ma", "Faith", "iMi", "PDLIF"]
    },
    "Billie Eilish": {
        "genre": "Pop",
        "tracks": ["bad guy", "everything i wanted", "Happier Than Ever",
                    "when the party's over", "lovely", "Therefore I Am",
                    "ocean eyes", "bury a friend", "No Time To Die",
                    "Oxytocin", "Lost Cause", "Your Power", "LUNCH",
                    "BIRDS OF A FEATHER", "WILDFLOWER", "THE GREATEST"]
    },
    "Massive Attack": {
        "genre": "Trip-Hop",
        "tracks": ["Teardrop", "Angel", "Unfinished Sympathy", "Safe from Harm",
                    "Inertia Creeps", "Dissolved Girl", "Risingson", "Protection",
                    "Black Milk", "Mezzanine", "Pray for Rain", "Voodoo in My Blood"]
    },
    "Aphex Twin": {
        "genre": "IDM/Electronic",
        "tracks": ["Avril 14th", "Windowlicker", "Xtal", "#1",
                    "Alberto Balsalm", "Flim", "4", "Polynomial-C",
                    "minipops 67", "CIRCLONT6A", "T69 collapse", "aisatsana"]
    },
    "SZA": {
        "genre": "R&B",
        "tracks": ["Kill Bill", "Snooze", "Love Galore", "The Weekend",
                    "Good Days", "Kiss Me More", "Shirt", "Nobody Gets Me",
                    "Broken Clocks", "Supermodel", "Normal Girl", "Saturn"]
    },
    "Gorillaz": {
        "genre": "Alternative/Electronic",
        "tracks": ["Feel Good Inc.", "Clint Eastwood", "On Melancholy Hill",
                    "Stylo", "DARE", "El Mañana", "Kids with Guns",
                    "Empire Ants", "Rhinestone Eyes", "Aries", "Strange Timez",
                    "New Gold", "Silent Running", "Cracker Island"]
    },
    "Portishead": {
        "genre": "Trip-Hop",
        "tracks": ["Glory Box", "Sour Times", "Wandering Star", "Roads",
                    "Numb", "Over", "Only You", "The Rip", "Machine Gun",
                    "Threads", "Silence", "We Carry On"]
    },
    "James Blake": {
        "genre": "Electronic/R&B",
        "tracks": ["Retrograde", "Limit to Your Love", "The Wilhelm Scream",
                    "Life Round Here", "Overgrown", "I Need a Forest Fire",
                    "Mile High", "Assume Form", "Are You Even Real?",
                    "Say What You Will", "Loading", "Coming Back"]
    },
    "Childish Gambino": {
        "genre": "Hip-Hop/R&B",
        "tracks": ["Redbone", "3005", "This Is America", "Feels Like Summer",
                    "Heartbeat", "Sweatpants", "Sober", "Terrified",
                    "IV. Sweatpants", "Algorythm", "Time", "Lithonia"]
    },
    "Boards of Canada": {
        "genre": "IDM/Ambient",
        "tracks": ["Roygbiv", "Dayvan Cowboy", "Everything You Do Is a Balloon",
                    "Music Is Math", "Turquoise Hexagon Sun", "Happy Cycling",
                    "Reach for the Dead", "Jacquard Causeway", "Palace Posy",
                    "New Seeds", "Chromakey Dreamcoat", "Satellite Anthem Icarus"]
    },
    "Beach House": {
        "genre": "Dream Pop",
        "tracks": ["Space Song", "Myth", "Silver Soul", "Zebra",
                    "Lazuli", "Depression Cherry", "PPP", "Lemon Glow",
                    "Dark Spring", "Once Twice Melody", "Superstar",
                    "New Romance", "Hurts to Love", "Many Nights"]
    }
}


# Approximate release year per track (used so nobody listens to a song before it exists)
YEARS = {
 "Radiohead": {"Creep":1992,"Karma Police":1997,"No Surprises":1997,"Everything In Its Right Place":2000,"Idioteque":2000,"Paranoid Android":1997,"Lucky":1997,"Exit Music (For a Film)":1997,"How to Disappear Completely":2000,"There There":2003,"15 Step":2007,"Reckoner":2007,"Lotus Flower":2011,"Bloom":2011,"Burn the Witch":2016,"Daydreaming":2016},
 "Kendrick Lamar": {"HUMBLE.":2017,"DNA.":2017,"Alright":2015,"King Kunta":2015,"Swimming Pools":2012,"Money Trees":2012,"m.A.A.d city":2012,"Poetic Justice":2012,"LOVE.":2017,"ELEMENT.":2017,"LOYALTY.":2017,"United in Grief":2022,"Die Hard":2022,"N95":2022,"Rich Spirit":2022,"Not Like Us":2024,"Euphoria":2024},
 "Tame Impala": {"The Less I Know the Better":2015,"Let It Happen":2015,"Feels Like We Only Go Backwards":2012,"Elephant":2012,"New Person, Same Old Mistakes":2015,"Borderline":2019,"Lost in Yesterday":2020,"Is It True":2020,"Breathe Deeper":2020,"One More Year":2020},
 "Arctic Monkeys": {"Do I Wanna Know?":2013,"R U Mine?":2013,"505":2007,"Fluorescent Adolescent":2007,"I Bet You Look Good on the Dancefloor":2005,"When the Sun Goes Down":2006,"Crying Lightning":2009,"Cornerstone":2009,"Why'd You Only Call Me When You're High?":2013,"Four Out of Five":2018,"Tranquility Base Hotel + Casino":2018,"Body Paint":2022,"There'd Better Be a Mirrorball":2022,"Sculptures of Anything Goes":2022},
 "Frank Ocean": {"Thinkin Bout You":2012,"Nights":2016,"Pink + White":2016,"Self Control":2016,"Ivy":2016,"Pyramids":2012,"Swim Good":2011,"Novacane":2011,"Lost":2012,"Chanel":2017,"Nikes":2016,"Solo":2016,"White Ferrari":2016,"Godspeed":2016},
 "Daft Punk": {"Get Lucky":2013,"Around the World":1997,"One More Time":2000,"Harder Better Faster Stronger":2001,"Instant Crush":2013,"Lose Yourself to Dance":2013,"Something About Us":2001,"Digital Love":2001,"Veridis Quo":2001,"Giorgio by Moroder":2013,"Touch":2013,"Within":2013,"Beyond":2013,"Give Life Back to Music":2013},
 "The Weeknd": {"Blinding Lights":2019,"Starboy":2016,"The Hills":2015,"Can't Feel My Face":2015,"Save Your Tears":2020,"After Hours":2020,"Heartless":2019,"In Your Eyes":2020,"Call Out My Name":2018,"I Feel It Coming":2016,"Die For You":2016,"Take My Breath":2021,"Sacrifice":2022,"Less Than Zero":2022,"Popular":2023},
 "Mac DeMarco": {"Chamber of Reflection":2014,"My Old Man":2017,"Salad Days":2014,"Freaking Out the Neighborhood":2012,"Let My Baby Stay":2014,"Still Beating":2017,"On the Level":2017,"This Old Dog":2017,"Nobody":2019,"All of Our Yesterdays":2019,"Heart to Heart":2019},
 "Tyler, The Creator": {"See You Again":2017,"EARFQUAKE":2019,"NEW MAGIC WAND":2019,"A BOY IS A GUN*":2019,"IFHY":2013,"Answer":2013,"Yonkers":2011,"She":2011,"Tamale":2013,"LUMBERJACK":2021,"WUSYANAME":2021,"SWEET / I THOUGHT YOU WANTED TO DANCE":2021,"SORRY NOT SORRY":2023,"DOGTOOTH":2023,"Noid":2024,"St. Chroma":2024},
 "Bon Iver": {"Skinny Love":2007,"Holocene":2011,"Re: Stacks":2007,"Flume":2007,"Perth":2011,"Towers":2011,"Calgary":2011,"22 (OVER S∞∞N)":2016,"8 (circle)":2016,"Hey, Ma":2019,"Faith":2019,"iMi":2019,"PDLIF":2020},
 "Billie Eilish": {"bad guy":2019,"everything i wanted":2019,"Happier Than Ever":2021,"when the party's over":2018,"lovely":2018,"Therefore I Am":2020,"ocean eyes":2016,"bury a friend":2019,"No Time To Die":2020,"Oxytocin":2021,"Lost Cause":2021,"Your Power":2021,"LUNCH":2024,"BIRDS OF A FEATHER":2024,"WILDFLOWER":2024,"THE GREATEST":2024},
 "Massive Attack": {"Teardrop":1998,"Angel":1998,"Unfinished Sympathy":1991,"Safe from Harm":1991,"Inertia Creeps":1998,"Dissolved Girl":1998,"Risingson":1998,"Protection":1994,"Black Milk":1998,"Mezzanine":1998,"Pray for Rain":2010,"Voodoo in My Blood":2016},
 "Aphex Twin": {"Avril 14th":2001,"Windowlicker":1999,"Xtal":1992,"#1":1994,"Alberto Balsalm":1995,"Flim":1997,"4":1996,"Polynomial-C":1992,"minipops 67":2014,"CIRCLONT6A":2014,"T69 collapse":2018,"aisatsana":2012},
 "SZA": {"Kill Bill":2022,"Snooze":2022,"Love Galore":2017,"The Weekend":2017,"Good Days":2020,"Kiss Me More":2021,"Shirt":2022,"Nobody Gets Me":2022,"Broken Clocks":2017,"Supermodel":2017,"Normal Girl":2017,"Saturn":2024},
 "Gorillaz": {"Feel Good Inc.":2005,"Clint Eastwood":2001,"On Melancholy Hill":2010,"Stylo":2010,"DARE":2005,"El Mañana":2005,"Kids with Guns":2005,"Empire Ants":2010,"Rhinestone Eyes":2010,"Aries":2020,"Strange Timez":2020,"New Gold":2022,"Silent Running":2023,"Cracker Island":2022},
 "Portishead": {"Glory Box":1994,"Sour Times":1994,"Wandering Star":1994,"Roads":1994,"Numb":1994,"Over":1997,"Only You":1997,"The Rip":2008,"Machine Gun":2008,"Threads":2008,"Silence":2008,"We Carry On":2008},
 "James Blake": {"Retrograde":2013,"Limit to Your Love":2010,"The Wilhelm Scream":2011,"Life Round Here":2013,"Overgrown":2013,"I Need a Forest Fire":2016,"Mile High":2019,"Assume Form":2019,"Are You Even Real?":2020,"Say What You Will":2021,"Loading":2023,"Coming Back":2021},
 "Childish Gambino": {"Redbone":2016,"3005":2013,"This Is America":2018,"Feels Like Summer":2018,"Heartbeat":2011,"Sweatpants":2013,"Sober":2014,"Terrified":2016,"IV. Sweatpants":2013,"Algorythm":2020,"Time":2020,"Lithonia":2024},
 "Boards of Canada": {"Roygbiv":1998,"Dayvan Cowboy":2005,"Everything You Do Is a Balloon":1996,"Music Is Math":2002,"Turquoise Hexagon Sun":1998,"Happy Cycling":1998,"Reach for the Dead":2013,"Jacquard Causeway":2013,"Palace Posy":2013,"New Seeds":2013,"Chromakey Dreamcoat":2005,"Satellite Anthem Icarus":2005},
 "Beach House": {"Space Song":2015,"Myth":2012,"Silver Soul":2010,"Zebra":2010,"Lazuli":2012,"Depression Cherry":2015,"PPP":2015,"Lemon Glow":2018,"Dark Spring":2018,"Once Twice Melody":2022,"Superstar":2022,"New Romance":2022,"Hurts to Love":2022,"Many Nights":2022},
}
LONG = {"Pyramids":593,"Giorgio by Moroder":544,"Touch":498,"Idioteque":309,"Windowlicker":367,"Dayvan Cowboy":300,"Unfinished Sympathy":318,"Paranoid Android":386,"How to Disappear Completely":356,"Machine Gun":283,"Let It Happen":467,"Once Twice Melody":331,"Avril 14th":125,"Flim":178,"Nights":307,"Kill Bill":153,"Creep":238,"Tranquility Base Hotel + Casino":215}
BASE_DUR = {"Alternative Rock":270,"Hip-Hop":230,"Psychedelic Pop":260,"Indie Rock":215,"R&B":250,"Electronic":300,"R&B/Pop":220,"Indie Pop":200,"Indie Folk":260,"Pop":205,"Trip-Hop":290,"IDM/Electronic":300,"IDM/Ambient":320,"Dream Pop":275,"Alternative/Electronic":240,"Electronic/R&B":255,"Hip-Hop/R&B":235}
import hashlib
def duration(artist, track):
    if track in LONG: return LONG[track]
    h = int(hashlib.md5((artist+"|"+track).encode()).hexdigest(), 16)
    base = BASE_DUR[LIBRARY[artist]["genre"]]
    return int(base * (0.72 + (h % 1000) / 1000 * 0.6))          # fixed per track, 0.72x .. 1.32x of the genre norm

# Taste arcs: each artist has one or more obsession windows (start month index from 2016-01, length in months, peak weight)
ARCS = {
 "Arctic Monkeys": [(0, 14, 9), (63, 10, 5)],
 "Radiohead": [(0, 26, 8), (74, 5, 2)],
 "Daft Punk": [(0, 10, 6), (49, 5, 4)],
 "Gorillaz": [(2, 12, 4), (53, 8, 2)],
 "Tame Impala": [(6, 14, 5), (28, 16, 8), (60, 8, 3)],
 "Mac DeMarco": [(9, 20, 5), (40, 6, 3)],
 "Massive Attack": [(10, 18, 4)],
 "Frank Ocean": [(18, 22, 9), (48, 10, 4)],
 "Bon Iver": [(19, 14, 6), (70, 8, 3)],
 "Portishead": [(22, 12, 4), (76, 6, 3)],
 "Boards of Canada": [(24, 10, 3), (50, 10, 4)],
 "James Blake": [(26, 60, 4), (62, 14, 6)],
 "Tyler, The Creator": [(32, 12, 6), (43, 18, 10), (70, 12, 6)],
 "Childish Gambino": [(30, 16, 6)],
 "Kendrick Lamar": [(15, 8, 5), (33, 10, 5), (76, 16, 10)],
 "Aphex Twin": [(36, 8, 3), (52, 12, 5), (84, 6, 3)],
 "Billie Eilish": [(38, 18, 7), (66, 6, 3)],
 "The Weeknd": [(44, 16, 8)],
 "Beach House": [(48, 46, 5), (73, 12, 8)],
 "SZA": [(42, 8, 3), (60, 12, 6), (83, 13, 11)],
}
START = datetime(2016, 1, 1); END = datetime(2023, 12, 31)

def month_index(d): return (d.year - 2016) * 12 + d.month - 1

def weight(artist, d):
    m = month_index(d) + d.day / 31; w = 0.15
    for s, ln, peak in ARCS[artist]:
        if s - 1.5 <= m <= s + ln + 3:
            ramp = min(1.0, max(0.0, (m - s + 1.5) / 2.5))          # ~2 months to peak
            decay = 1.0 if m <= s + ln else max(0.0, 1 - (m - s - ln) / 3)
            w = max(w, peak * ramp * decay)
    return w

def available(artist, d):
    return [t for t in LIBRARY[artist]["tracks"] if YEARS[artist].get(t, 2000) <= d.year - (0 if d.month > 3 else 1)] or []

def generate():
    rows = []; d = START; last_top = None
    fav_tracks = {}                                               # per-artist favourite subset (people replay the same few songs)
    for a in LIBRARY: fav_tracks[a] = set(random.sample(LIBRARY[a]["tracks"], k=min(5, len(LIBRARY[a]["tracks"]))))
    vacation_until = None
    while d <= END:
        if vacation_until and d < vacation_until: d += timedelta(days=1); continue
        if random.random() < 0.012: vacation_until = d + timedelta(days=random.randint(4, 12))
        weekend = d.weekday() >= 5
        # sessions per day: 0 on quiet days, binge on some weekends
        p_quiet = 0.22 if not weekend else 0.12
        if random.random() < p_quiet: d += timedelta(days=1); continue
        n_sessions = random.choice([1, 1, 2, 2, 3]) + (1 if weekend else 0)
        slots = [(7, 11), (11, 16), (16, 20), (20, 24)]
        chosen = sorted(random.sample(slots, k=min(n_sessions, len(slots))))
        weights = {a: weight(a, d) for a in LIBRARY}
        for s0, s1 in chosen:
            t = d.replace(hour=random.randint(s0, s1 - 1), minute=random.randint(0, 59), second=random.randint(0, 59))
            n_tracks = random.randint(2, 9) if not weekend else random.randint(3, 14)
            artist = None
            while n_tracks > 0:
                if artist is None or random.random() < 0.35:       # switch artist; usually stay on the same one for a few songs
                    pool = list(weights); artist = random.choices(pool, weights=[weights[a] for a in pool])[0]
                tracks = available(artist, t)
                if not tracks: artist = None; continue
                favs = [x for x in tracks if x in fav_tracks[artist]]
                track = random.choice(favs) if favs and random.random() < 0.65 else random.choice(tracks)
                dur = duration(artist, track)
                pc = 1 if random.random() < 0.8 else random.choice([2, 2, 3])
                rows.append({"timestamp": t.strftime("%Y-%m-%d %H:%M:%S"), "artist": artist, "track": track,
                             "genre": LIBRARY[artist]["genre"], "duration_sec": dur, "play_count": pc})
                t += timedelta(seconds=dur * pc + random.randint(3, 40)); n_tracks -= 1
                if t.day != d.day: break
        d += timedelta(days=1)
    rows.sort(key=lambda x: x["timestamp"])
    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "artist", "track", "genre", "duration_sec", "play_count"]); w.writeheader(); w.writerows(rows)
    print(f"Generated {len(rows)} listening events -> {out}")
    print(f"Date range: {rows[0]['timestamp']} — {rows[-1]['timestamp']}")
    print(f"Unique artists: {len(set(r['artist'] for r in rows))}  Unique tracks: {len(set(r['track'] for r in rows))}")

if __name__ == "__main__":
    generate()
