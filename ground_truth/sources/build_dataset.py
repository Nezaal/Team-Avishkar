"""
SIH26166 Ground Truth Dataset Builder
Builds all CSVs, JSONs, and per-pair metadata from source coordinate files.
All control points are GEOSPATIALLY DERIVED - not manually measured pixels.
"""
import csv, json, math, os
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAIRS_DIR = os.path.join(ROOT, "pairs")
CONTROL_POINTS_DIR = os.path.join(ROOT, "control_points")
MANIFESTS_DIR = os.path.join(ROOT, "manifests")
METADATA_DIR = os.path.join(ROOT, "metadata")
VALIDATION_DIR = os.path.join(ROOT, "validation")
SYNTHETIC_DIR = os.path.join(VALIDATION_DIR, "synthetic")
NOW = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
DATE = datetime.utcnow().strftime("%Y-%m-%d")

OHRC_SCENES = [
    ("ch2_ohr_ncp_20190906T1246532096_d_img_d18",-14.323756,71.334305,-16.72985,69.174869,-14.735024,71.445725,-17.15629,69.299801,63230,12000,0.27),
    ("ch2_ohr_ncp_20200229T0739312111_d_img_d18",-74.36605,43.709461,-74.357976,43.359488,-73.52454,43.957706,-73.516771,43.625522,93693,12000,0.22977),
    ("ch2_ohr_ncp_20200229T0938004033_d_img_d32",-73.920405,42.799376,-73.912522,42.457137,-73.078883,43.031644,-73.071384,42.706306,93693,12000,0.23022),
    ("ch2_ohr_ncp_20200824T0806596861_d_img_d18",-61.610358,56.580435,-61.604458,56.804725,-62.441705,56.641651,-62.435771,56.871902,90148,12000,0.25856),
    ("ch2_ohr_ncp_20200824T1003365280_d_img_d18",-61.660467,56.577047,-61.657424,56.807375,-62.490045,56.666465,-62.486906,56.902936,93692,12000,0.25810),
    ("ch2_ohr_ncp_20200825T1127278043_d_img_d18",-68.36261,41.141334,-68.35982,41.420493,-69.197495,41.19252,-69.194672,41.482045,93693,12000,0.24950),
    ("ch2_ohr_ncp_20200825T1322594314_d_img_d18",-63.322785,39.459103,-63.322421,39.705735,-64.156508,39.482354,-64.156265,39.736163,90148,12000,0.25141),
    ("ch2_ohr_ncp_20200825T1521048453_d_img_d18",-68.334774,41.076553,-68.334153,41.367581,-69.165951,41.203266,-69.165367,41.505086,93692,12000,0.25083),
    ("ch2_ohr_ncp_20200825T1716291272_d_img_d18",-63.339232,39.451651,-63.338565,39.696512,-64.170288,39.532475,-64.16989,39.78442,93693,12000,0.25251),
    ("ch2_ohr_ncp_20200826T0459464752_d_img_d18",-65.800042,31.694944,-65.792962,31.958737,-66.631675,31.738132,-66.62493,32.010558,93693,12000,0.25098),
    ("ch2_ohr_ncp_20200826T0853204550_d_img_d18",-65.8165,31.575842,-65.815683,31.85681,-66.645939,31.68509,-66.644387,31.975172,93692,12000,0.25040),
    ("ch2_ohr_ncp_20200827T0030107497_d_img_d18",-67.897927,20.805164,-67.89231,21.069171,-68.737545,20.848896,-68.731806,21.122556,101075,12000,0.23696),
    ("ch2_ohr_ncp_20200827T0226453039_d_img_d18",-67.911042,20.77073,-67.912566,21.042945,-68.749286,20.841259,-68.750647,21.123279,101075,12000,0.23579),
    ("ch2_ohr_ncp_20200827T0423073950_d_img_d18",-64.70883,20.009509,-64.693345,20.268058,-65.548369,20.083487,-65.532729,20.34999,93693,12000,0.23498),
    ("ch2_ohr_ncp_20200827T0619368134_d_img_d18",-64.725745,19.994568,-64.730465,20.283444,-65.563102,20.100913,-65.567546,20.398743,91971,12000,0.23424),
    ("ch2_ohr_ncp_20210331T2033243734_d_img_d18",-19.694932,41.406534,-19.695877,41.523235,-20.524168,41.414143,-20.525091,41.53149,90148,12000,0.26788),
    ("ch2_ohr_ncp_20210401T2200364910_d_img_d18",-12.941111,25.162308,-12.962214,25.303328,-13.770325,25.154024,-13.791494,25.295565,76619,12000,0.26595),
    ("ch2_ohr_ncp_20210401T2357376656_d_img_d18",-13.058433,25.133115,-13.055345,25.245912,-13.888916,25.128422,-13.885844,25.241643,90148,12000,0.26489),
    ("ch2_ohr_ncp_20210402T0155096873_d_img_d18",-12.908266,25.167224,-12.91129,25.279036,-13.739114,25.166372,-13.742124,25.278594,90148,12000,0.26383),
    ("ch2_ohr_ncp_20210402T0546284043_d_img_d18",1.056037,23.375034,1.068878,23.495434,0.224735,23.371989,0.237605,23.492393,78175,12000,0.26104),
    ("ch2_ohr_ncp_20210405T0442095110_d_img_d18",-68.279963,341.27492,-68.277167,341.545178,-69.121165,341.201487,-69.118497,341.481891,101075,12000,0.23100),
    ("ch2_ohr_ncp_20210405T0640233469_d_img_d18",-68.275788,341.268936,-68.281299,341.539077,-69.119599,341.23616,-69.125154,341.516475,93693,12000,0.22915),
]

TMC2_SCENES = {
    "TMC-A":{"name":"ch2_tmc_ncn_SouthPolar_41E_grd","note":"IIT confirmed. 6x OHRC overlap. ~68-69S,40-42E. Exact product ID: run IIT overlap script.","ul_lat":-67.5,"ul_lon":40.0,"ur_lat":-67.5,"ur_lon":42.5,"ll_lat":-70.0,"ll_lon":40.0,"lr_lat":-70.0,"lr_lon":42.5,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-B":{"name":"ch2_tmc_ncn_SouthPolar_43E_grd","note":"IIT confirmed. ~73-74S,42-44E. Exact product ID: run IIT overlap script.","ul_lat":-72.5,"ul_lon":42.0,"ur_lat":-72.5,"ur_lon":44.5,"ll_lat":-75.0,"ll_lon":42.0,"lr_lat":-75.0,"lr_lon":44.5,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-C":{"name":"ch2_tmc_ncn_Southern_56E_grd","note":"IIT confirmed. ~61-63S,56-57E. Exact product ID: run IIT overlap script.","ul_lat":-60.5,"ul_lon":56.0,"ur_lat":-60.5,"ur_lon":57.2,"ll_lat":-63.0,"ll_lon":56.0,"lr_lat":-63.0,"lr_lon":57.2,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-D":{"name":"ch2_tmc_ncn_Southern_39E_grd","note":"IIT confirmed. ~63-65S,39-40E. Exact product ID: run IIT overlap script.","ul_lat":-62.5,"ul_lon":39.0,"ur_lat":-62.5,"ur_lon":40.0,"ll_lat":-65.5,"ll_lon":39.0,"lr_lat":-65.5,"lr_lon":40.0,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-E":{"name":"ch2_tmc_ncn_Southern_31E_grd","note":"IIT confirmed. ~65-67S,31-32E. Exact product ID: run IIT overlap script.","ul_lat":-65.0,"ul_lon":31.0,"ur_lat":-65.0,"ur_lon":32.5,"ll_lat":-67.5,"ll_lon":31.0,"lr_lat":-67.5,"lr_lon":32.5,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-F":{"name":"ch2_tmc_ncn_SouthPolar_20E_grd","note":"IIT confirmed + USGS/ASP region. ~64-69S,20-21E. LOLA independent ref available.","ul_lat":-64.0,"ul_lon":19.5,"ur_lat":-64.0,"ur_lon":21.5,"ll_lat":-69.5,"ll_lon":19.5,"lr_lat":-69.5,"lr_lon":21.5,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-USGS":{"name":"ch2_tmc_ndn_20231101T0125121377_d_oth_d18","note":"USGS/ASP explicitly documented OTH product. LOLA DEM comparison documented.","ul_lat":-67.0,"ul_lon":19.5,"ur_lat":-67.0,"ur_lon":22.0,"ll_lat":-71.0,"ll_lon":19.5,"lr_lat":-71.0,"lr_lon":22.0,"pix_res_m":5.0,"product":"OTH/DTM","url":"https://stereopipeline.readthedocs.io/en/latest/examples/chandrayaan2.html"},
    "TMC-NP":{"name":"ch2_tmc_ncn_SouthPolar_341E_grd","note":"IIT implied. ~68-69S,341E (=-19W). Exact product ID: run IIT overlap script.","ul_lat":-67.5,"ul_lon":340.5,"ur_lat":-67.5,"ur_lon":342.0,"ll_lat":-70.0,"ll_lon":340.5,"lr_lat":-70.0,"lr_lon":342.0,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-MID1":{"name":"ch2_tmc_ncn_MidSouth_41E_grd","note":"Inferred. ~19-21S,41E. Exact product ID: run IIT overlap script.","ul_lat":-19.0,"ul_lon":41.0,"ur_lat":-19.0,"ur_lon":42.0,"ll_lat":-21.0,"ll_lon":41.0,"lr_lat":-21.0,"lr_lon":42.0,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-MID2":{"name":"ch2_tmc_ncn_MidSouth_25E_grd","note":"Inferred. ~12-14S,25E. Exact product ID: run IIT overlap script.","ul_lat":-12.0,"ul_lon":24.8,"ur_lat":-12.0,"ur_lon":25.5,"ll_lat":-14.0,"ll_lon":24.8,"lr_lat":-14.0,"lr_lon":25.5,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
    "TMC-EQ":{"name":"ch2_tmc_ncn_Equatorial_70E_grd","note":"Inferred. ~14-17S,69-71E. Exact product ID: run IIT overlap script.","ul_lat":-13.5,"ul_lon":68.5,"ur_lat":-13.5,"ur_lon":71.8,"ll_lat":-17.5,"ll_lon":68.5,"lr_lat":-17.5,"lr_lon":71.8,"pix_res_m":5.0,"product":"GRD","url":"https://pradan.issdc.gov.in/ch2/"},
}

PAIRS = [
    {"ohrc_idx":5,"tmc_key":"TMC-A","region":"South_Polar_41E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. USGS/ASP similar region. Best south-polar pair."},
    {"ohrc_idx":7,"tmc_key":"TMC-A","region":"South_Polar_41E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. Parallel OHRC track 2h later over TMC-A."},
    {"ohrc_idx":1,"tmc_key":"TMC-B","region":"South_Polar_43E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. ~73-74S extreme latitude."},
    {"ohrc_idx":2,"tmc_key":"TMC-B","region":"South_Polar_43E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. d32 product same region."},
    {"ohrc_idx":3,"tmc_key":"TMC-C","region":"Southern_56E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. ~61-62S, 56E."},
    {"ohrc_idx":4,"tmc_key":"TMC-C","region":"Southern_56E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. Parallel track 2h later."},
    {"ohrc_idx":6,"tmc_key":"TMC-D","region":"Southern_39E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. ~63-64S, 39E."},
    {"ohrc_idx":8,"tmc_key":"TMC-D","region":"Southern_39E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. Parallel track 2h later."},
    {"ohrc_idx":9,"tmc_key":"TMC-E","region":"Southern_31E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. ~65-66S, 31E. Distinct longitude."},
    {"ohrc_idx":10,"tmc_key":"TMC-E","region":"Southern_31E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. ~66S, 31E, parallel track."},
    {"ohrc_idx":11,"tmc_key":"TMC-F","region":"South_Polar_20E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. USGS/ASP documented region ~20E. LOLA available."},
    {"ohrc_idx":12,"tmc_key":"TMC-USGS","region":"South_Polar_20E_USGS","quality":"B","gt_type":"GEOREFERENCED_REFERENCE","overlap":"confirmed_overlap","notes":"USGS/ASP explicitly documented. TMC-2 OTH product named in ASP docs. LOLA comparison documented."},
    {"ohrc_idx":13,"tmc_key":"TMC-F","region":"South_Polar_20E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. ~64-65S, 20E."},
    {"ohrc_idx":14,"tmc_key":"TMC-F","region":"South_Polar_20E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"IIT confirmed. Parallel track, ~20E south polar."},
    {"ohrc_idx":0,"tmc_key":"TMC-EQ","region":"Equatorial_South_70E","quality":"C","gt_type":"DERIVED_CORRESPONDENCE","overlap":"probable_overlap","notes":"2019 OHRC. Earliest scene. Overlap inferred from coordinates."},
    {"ohrc_idx":15,"tmc_key":"TMC-MID1","region":"Mid_South_41E","quality":"C","gt_type":"DERIVED_CORRESPONDENCE","overlap":"inferred_overlap","notes":"2021 OHRC. ~19-21S, 41E. Different epoch."},
    {"ohrc_idx":16,"tmc_key":"TMC-MID2","region":"Mid_South_25E","quality":"C","gt_type":"DERIVED_CORRESPONDENCE","overlap":"inferred_overlap","notes":"2021 OHRC. ~12-14S, 25E. Different region."},
    {"ohrc_idx":17,"tmc_key":"TMC-MID2","region":"Mid_South_25E","quality":"C","gt_type":"DERIVED_CORRESPONDENCE","overlap":"inferred_overlap","notes":"2021 OHRC parallel track over TMC-MID2."},
    {"ohrc_idx":20,"tmc_key":"TMC-NP","region":"South_Polar_341E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"2021 OHRC. ~68-69S, 341E (W hemisphere). Maximum longitudinal diversity."},
    {"ohrc_idx":21,"tmc_key":"TMC-NP","region":"South_Polar_341E","quality":"B","gt_type":"DERIVED_CORRESPONDENCE","overlap":"confirmed_overlap","notes":"2021 OHRC parallel track, 341E south polar."},
]

def latlon_to_pixel(lat, lon, ul_lat,ul_lon, ur_lat,ur_lon, ll_lat,ll_lon, lr_lat,lr_lon, width, height):
    s, t = 0.5, 0.5
    for _ in range(25):
        bla = (1-s)*(1-t)*ul_lat + s*(1-t)*ur_lat + (1-s)*t*ll_lat + s*t*lr_lat
        blo = (1-s)*(1-t)*ul_lon + s*(1-t)*ur_lon + (1-s)*t*ll_lon + s*t*lr_lon
        dla_ds = -(1-t)*ul_lat + (1-t)*ur_lat - t*ll_lat + t*lr_lat
        dlo_ds = -(1-t)*ul_lon + (1-t)*ur_lon - t*ll_lon + t*lr_lon
        dla_dt = -(1-s)*ul_lat - s*ur_lat + (1-s)*ll_lat + s*lr_lat
        dlo_dt = -(1-s)*ul_lon - s*ur_lon + (1-s)*ll_lon + s*lr_lon
        det = dla_ds*dlo_dt - dlo_ds*dla_dt
        if abs(det) < 1e-12: break
        ds = -(( bla-lat)*dlo_dt - (blo-lon)*dla_dt) / det
        dt = -(dla_ds*(blo-lon) - dlo_ds*(bla-lat)) / det
        s = max(0.0,min(1.0,s+ds*0.5)); t = max(0.0,min(1.0,t+dt*0.5))
    return round(s*(width-1),1), round(t*(height-1),1)

def generate_control_points(pair_id, ohrc, tmc, n_grid=6):
    ul_lat,ul_lon = ohrc[1],ohrc[2]; ur_lat,ur_lon = ohrc[3],ohrc[4]
    ll_lat,ll_lon = ohrc[5],ohrc[6]; lr_lat,lr_lon = ohrc[7],ohrc[8]
    w,h = ohrc[9],ohrc[10]
    lat_min = max(min(ll_lat,lr_lat), min(tmc["ll_lat"],tmc["lr_lat"]))
    lat_max = min(max(ul_lat,ur_lat), max(tmc["ul_lat"],tmc["ur_lat"]))
    lon_min = max(min(ul_lon,ll_lon), min(tmc["ul_lon"],tmc["ll_lon"]))
    lon_max = min(max(ur_lon,lr_lon), max(tmc["ur_lon"],tmc["lr_lon"]))
    if lat_min >= lat_max or lon_min >= lon_max: return []
    pts = []
    for i in range(1, n_grid+1):
        for j in range(1, n_grid+1):
            lat = lat_min + i*(lat_max-lat_min)/(n_grid+1)
            lon = lon_min + j*(lon_max-lon_min)/(n_grid+1)
            sx,sy = latlon_to_pixel(lat,lon, ul_lat,ul_lon, ur_lat,ur_lon, ll_lat,ll_lon, lr_lat,lr_lon, w,h)
            pts.append({"pair_id":pair_id,"point_id":f"P{len(pts)+1:03d}","source_x":sx,"source_y":sy,
                        "reference_x":"UNKNOWN","reference_y":"UNKNOWN",
                        "latitude":round(lat,6),"longitude":round(lon,6),
                        "source":"IIT_InterIIT_bilinear_interpolation",
                        "verification_method":"geospatially_derived",
                        "accuracy":"sub-degree_geographic_only",
                        "coordinate_system":"selenographic_IAU2015",
                        "independent":"false",
                        "notes":"Bilinear interp from OHRC corner coords. NOT manually verified. TMC-2 pixel NOT computed (image dims unavailable)."})
    return pts

pairs_rows=[]; validation_rows=[]; all_cps={}
for i,pd_def in enumerate(PAIRS):
    pid = f"pair_{i+1:03d}"
    ohrc = OHRC_SCENES[pd_def["ohrc_idx"]]
    tmc = TMC2_SCENES[pd_def["tmc_key"]]
    pair_dir = os.path.join(PAIRS_DIR, pid)
    os.makedirs(os.path.join(pair_dir,"raw"),exist_ok=True)
    os.makedirs(os.path.join(pair_dir,"processed"),exist_ok=True)
    cps = generate_control_points(pid, ohrc, tmc, 6)
    all_cps[pid] = len(cps)
    if cps:
        with open(os.path.join(CONTROL_POINTS_DIR,f"{pid}.csv"),"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cps[0].keys()); w.writeheader(); w.writerows(cps)
    lat_min=max(min(ohrc[5],ohrc[7]),min(tmc["ll_lat"],tmc["lr_lat"]))
    lat_max=min(max(ohrc[1],ohrc[3]),max(tmc["ul_lat"],tmc["ur_lat"]))
    lon_min=max(min(ohrc[2],ohrc[6]),min(tmc["ul_lon"],tmc["ll_lon"]))
    lon_max=min(max(ohrc[4],ohrc[8]),max(tmc["ur_lon"],tmc["lr_lon"]))
    gt_type=pd_def["gt_type"]; quality=pd_def["quality"]
    overlap_ok=pd_def["overlap"] in ("confirmed_overlap","probable_overlap")
    indep = gt_type=="GEOREFERENCED_REFERENCE"
    meta={
        "pair_id":pid,"source":{"sensor":"OHRC","filename":ohrc[0],"url":"https://pradan.issdc.gov.in/ch2/ (login required)",
            "width":ohrc[9],"height":ohrc[10],"resolution_m":ohrc[11],"coordinate_system":"selenographic_IAU2015",
            "ul_lat":ohrc[1],"ul_lon":ohrc[2],"ur_lat":ohrc[3],"ur_lon":ohrc[4],"ll_lat":ohrc[5],"ll_lon":ohrc[6],"lr_lat":ohrc[7],"lr_lon":ohrc[8]},
        "reference":{"sensor":"TMC-2","filename":tmc["name"],"url":tmc["url"],"width":None,"height":None,
            "resolution_m":tmc["pix_res_m"],"product":tmc["product"],"coordinate_system":"selenographic_IAU2015",
            "ul_lat":tmc["ul_lat"],"ul_lon":tmc["ul_lon"],"ur_lat":tmc["ur_lat"],"ur_lon":tmc["ur_lon"],
            "ll_lat":tmc["ll_lat"],"ll_lon":tmc["ll_lon"],"lr_lat":tmc["lr_lat"],"lr_lon":tmc["lr_lon"]},
        "region":pd_def["region"],"overlap":pd_def["overlap"],
        "ground_truth_type":gt_type,"quality_level":quality,
        "independent_reference":indep,"independent_reference_note":"LOLA available for GEOREFERENCED_REFERENCE pairs only.",
        "control_point_count":len(cps),"verification_method":"geospatially_derived",
        "accuracy":"sub-degree_geographic_only — NOT sub-pixel",
        "pixel_level_validation":"NO","subpixel_validation":"NO",
        "license":"ISRO PRADAN terms + Apache-2.0 (IIT CSV)",
        "download_status":"coordinates_available; images require PRADAN login",
        "notes":pd_def["notes"],"tmc_note":tmc["note"],"build_date":DATE,
        "data_source_primary":"jha04amartya/ISRO-InterIIT-Techmeet-11.0",
        "data_source_url":"https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0",
    }
    with open(os.path.join(pair_dir,"metadata.json"),"w",encoding="utf-8") as f: json.dump(meta,f,indent=2)
    readme_txt = f"""# {pid} — {pd_def['region']}

| Field | Value |
|-------|-------|
| OHRC | `{ohrc[0]}` |
| TMC-2 | `{tmc['name']}` |
| Quality | **{quality}** |
| GT Type | `{gt_type}` |
| Control Points | {len(cps)} (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | {'YES (LOLA)' if indep else 'NO'} |

## OHRC Sensor
- Resolution: {ohrc[11]:.4f} m/px | Dims: {ohrc[9]}×{ohrc[10]}px
- UL ({ohrc[1]:.4f}°,{ohrc[2]:.4f}°) UR ({ohrc[3]:.4f}°,{ohrc[4]:.4f}°)
- LL ({ohrc[5]:.4f}°,{ohrc[6]:.4f}°) LR ({ohrc[7]:.4f}°,{ohrc[8]:.4f}°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: {tmc['pix_res_m']} m/px | Product: {tmc['product']}
- Note: {tmc['note']}

## Ground Truth Classification: {gt_type}
{pd_def['notes']}

## ⚠ Critical Limitations
- Control points are GEOSPATIALLY DERIVED from corner coordinate interpolation
- TMC-2 pixel coordinates are UNKNOWN (image dimensions not in source CSV)
- NOT manually verified correspondences
- CANNOT support sub-pixel accuracy claims
- Images NOT downloaded (PRADAN login required)

## Directory Structure for Registration Pipeline
- `raw/`: **Only** for the original, unmodified `.img` files downloaded from ISRO PRADAN. 
- `processed/`: **Only** for CV pipeline outputs (e.g. SIFT keypoints, matching visualizations, homography matrices). No modified images are stored here.

```
raw/source_ohrc_{ohrc[0][:45]}.img  ← PRADAN download required
raw/reference_tmc2_{tmc['name'][:40]}.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
"""
    with open(os.path.join(pair_dir,"README.md"),"w",encoding="utf-8") as f: f.write(readme_txt)
    pairs_rows.append({
        "pair_id":pid,"source_image_id":ohrc[0],"reference_image_id":tmc["name"],
        "source_filename":ohrc[0]+".img","reference_filename":tmc["name"]+".img",
        "source_sensor":"OHRC","reference_sensor":"TMC-2","source_product":"IMG","reference_product":tmc["product"],
        "source_url":"https://pradan.issdc.gov.in/ch2/ (login required)","reference_url":tmc["url"],
        "region":pd_def["region"],
        "latitude_min":round(lat_min,5),"latitude_max":round(lat_max,5),
        "longitude_min":round(lon_min,5),"longitude_max":round(lon_max,5),
        "source_width":ohrc[9],"source_height":ohrc[10],
        "reference_width":"UNKNOWN","reference_height":"UNKNOWN",
        "source_resolution_m":ohrc[11],"reference_resolution_m":tmc["pix_res_m"],
        "overlap_available":"YES" if overlap_ok else "PROBABLE",
        "ground_truth_type":gt_type,"ground_truth_source":"IIT_InterIIT_11.0 + USGS_ASP",
        "independent_reference":"YES" if indep else "NO","control_point_count":len(cps),
        "coordinate_system":"selenographic_IAU2015","georeferencing_available":"YES",
        "verification_method":"geospatially_derived",
        "accuracy_claim":"sub-degree geographic only — NOT sub-pixel",
        "license":"ISRO PRADAN terms + Apache-2.0","download_status":"coordinates_only",
        "notes":pd_def["notes"],
    })
    validation_rows.append({
        "pair_id":pid,"ground_truth_type":gt_type,"control_point_count":len(cps),
        "independent":"YES" if indep else "NO","mean_reference_quality":quality,
        "spatial_coverage":f"6x6_grid_{len(cps)}_pts",
        "independent_reference":"YES" if indep else "NO",
        "pixel_level_validation":"NO","subpixel_validation":"NO",
        "recommended_for_mvp":"YES" if quality in ("A","B") and overlap_ok else "CONDITIONAL",
        "limitations":"Geospatially derived only. No manual annotation. TMC-2 pixel coords unknown. Images need PRADAN download.",
    })

with open(os.path.join(MANIFESTS_DIR,"pairs.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=pairs_rows[0].keys()); w.writeheader(); w.writerows(pairs_rows)
with open(os.path.join(MANIFESTS_DIR,"validation.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=validation_rows[0].keys()); w.writeheader(); w.writerows(validation_rows)

rejected_rows=[
    {"source":"IIT_InterIIT_11.0","pair_id":"R001","source_image":"ch2_ohr_ncp_20190906T1246532096 (equatorial 2019)","reference_image":"TMC-EQ","reason_rejected":"probable_overlap_only — IIT reported 18 confirmed pairs from south polar region; equatorial 2019 scene not confirmed by overlap script","url":"https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0","notes":"Retained as pair_015 at quality C with explicit caveat."},
    {"source":"IIT_InterIIT_11.0","pair_id":"R002","source_image":"ch2_ohr_ncp_20210401T2357376656_d_img_hw1","reference_image":"TMC-MID2","reason_rejected":"duplicate_scene — hw1 product nearly identical footprint to d18 from same timestamp","url":"https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0","notes":"Excluded to prevent scene duplication count inflation."},
    {"source":"IIT_InterIIT_11.0","pair_id":"R003","source_image":"ch2_ohr_ncp_20210402T0546284043 (+1N latitude)","reference_image":"TMC","reason_rejected":"insufficient_overlap — northernmost OHRC at +1N; TMC match uncertain; not in IIT 18-pair list","url":"https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0","notes":"Out-of-scope for south polar focus. Excluded."},
    {"source":"IIT_InterIIT_11.0","pair_id":"R004","source_image":"ch2_ohr_ncp_20210405T0442095110_d_img_d32","reference_image":"TMC-NP","reason_rejected":"duplicate_scene — d32 and d18 from same orbit, identical footprint","url":"https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0","notes":"Same footprint as pair_019 (d18). Excluded."},
    {"source":"PRADAN","pair_id":"R005","source_image":"ALL OHRC images","reference_image":"ALL TMC-2 images","reason_rejected":"unavailable_download — image pixels require ISRO PRADAN account; not freely downloadable","url":"https://pradan.issdc.gov.in/ch2/","notes":"Only corner coordinates (metadata) available without account. All CP pixel coords are geospatially derived only."},
    {"source":"LROC_NAC","pair_id":"R006","source_image":"LROC NAC imagery","reference_image":"OHRC/TMC-2","reason_rejected":"not_OHRC_TMC — LROC NAC is NASA/LRO instrument, not Chandrayaan-2; substitution not permitted","url":"https://lroc.im-ldi.com/data","notes":"LROC retained as INDEPENDENT REFERENCE only, not as image pair substitute."},
    {"source":"synthetic","pair_id":"R007","source_image":"synthetic_transformed_images","reference_image":"synthetic_transformed_images","reason_rejected":"synthetic — not real lunar pair; kept in separate validation/synthetic/ directory","url":"N/A","notes":"Exact GT but not real OHRC/TMC-2. Kept strictly separate from real pairs."},
]
with open(os.path.join(VALIDATION_DIR,"rejected.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=rejected_rows[0].keys()); w.writeheader(); w.writerows(rejected_rows)

syn_rows=[
    {"sample_id":"syn_001","source_image":"ch2_ohr_ncp_20200825T1127278043_d_img_d18","transformation_type":"translation","transformation_matrix":"[[1,0,150],[0,1,75],[0,0,1]]","parameters":"tx=150px,ty=75px","source_points":"6x6_grid_center_of_image","true_reference_points":"source_pts+[150,75]","notes":"Known translation. Exact GT. Use to validate pipeline coordinate handling."},
    {"sample_id":"syn_002","source_image":"ch2_ohr_ncp_20200825T1127278043_d_img_d18","transformation_type":"rotation","transformation_matrix":"[[cos5,-sin5,cx*(1-cos5)+cy*sin5],[sin5,cos5,cy*(1-cos5)-cx*sin5],[0,0,1]]","parameters":"angle=5deg,center=image_center","source_points":"6x6_grid","true_reference_points":"apply_rotation","notes":"5-degree rotation. Tests rotation recovery. Exact GT."},
    {"sample_id":"syn_003","source_image":"ch2_ohr_ncp_20200825T1127278043_d_img_d18","transformation_type":"scale","transformation_matrix":"[[0.85,0,0],[0,0.85,0],[0,0,1]]","parameters":"scale=0.85x","source_points":"6x6_grid","true_reference_points":"source_pts*0.85","notes":"15% scale. Partial model of OHRC/TMC resolution ratio. Exact GT."},
    {"sample_id":"syn_004","source_image":"ch2_ohr_ncp_20200825T1127278043_d_img_d18","transformation_type":"affine","transformation_matrix":"[[0.95,-0.05,100],[0.05,0.95,50],[0,0,1]]","parameters":"combined rotation+scale+translation","source_points":"6x6_grid","true_reference_points":"apply_affine","notes":"Mild affine. Models OHRC/TMC geometric relationship. Exact GT."},
    {"sample_id":"syn_005","source_image":"ch2_ohr_ncp_20200825T1521048453_d_img_d18","transformation_type":"mild_perspective","transformation_matrix":"[[1.02,0.01,80],[0.01,0.98,40],[0.000001,-0.000001,1]]","parameters":"mild_perspective_warp","source_points":"6x6_grid","true_reference_points":"apply_perspective","notes":"Mild perspective. Tests homography recovery. Different source for diversity. Exact GT."},
]
with open(os.path.join(SYNTHETIC_DIR,"synthetic_gt.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=syn_rows[0].keys()); w.writeheader(); w.writerows(syn_rows)

total_cps=sum(all_cps.values())
print(f"Pairs created: {len(PAIRS)}")
print(f"OHRC+TMC-2: {len(PAIRS)}")
print(f"With control points: {sum(1 for v in all_cps.values() if v>0)}")
print(f"Total control points: {total_cps}")
print(f"Independent refs: {sum(1 for p in PAIRS if p['gt_type']=='GEOREFERENCED_REFERENCE')}")
print(f"Quality B: {sum(1 for p in PAIRS if p['quality']=='B')}")
print(f"Quality C: {sum(1 for p in PAIRS if p['quality']=='C')}")
print("DONE")
