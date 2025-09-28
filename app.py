from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
import json
import os
import re
import httpx
from urllib.parse import quote

app = FastAPI()
kitsu_addon_url = 'https://anime-kitsu.strem.fun'


def json_response(data):
    response = JSONResponse(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Surrogate-Control"] = "no-store"
    return response


@app.get("/catalog/{type}/{id}.json")
@app.get("/catalog/{type}/{id}/{path}.json")
async def get_catalog(type: str, id: str, path: str):
    search_type = id.split('-')[-1]

    # Search query extration
    match = re.search(r"search=([^&]+)", path)
    if match:
        search_query = quote(match.group(1))  # URL encode
    else:
        search_query = ""
    
    # Skip extration
    match = re.search(r"skip=(\d+)", path)
    if match:
        skip = int(match.group(1))
    else:
        skip = 0

    print(skip)
    print(search_query)

    if search_type == 'movie':
        url = f"https://kitsu.io/api/edge/anime?filter[subtype]=movie&filter[text]={search_query}&page[limit]=20&page[offset]={skip}"
    elif search_type == 'show':
        url = f"https://kitsu.io/api/edge/anime?filter[subtype]=tv&filter[text]={search_query}&page[limit]=20&page[offset]={skip}"
    elif search_type == 'ova':
        url = f"https://kitsu.io/api/edge/anime?filter[subtype]=ova&filter[text]={search_query}&page[limit]=20&page[offset]={skip}"
    elif search_type == 'ona':
        url = f"https://kitsu.io/api/edge/anime?filter[subtype]=ona&filter[text]={search_query}&page[limit]=20&page[offset]={skip}"
    elif search_type == 'special':
        url = f"https://kitsu.io/api/edge/anime?filter[subtype]=special&filter[text]={search_query}&page[limit]=20&page[offset]={skip}"


    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            return json_response({"metas": []})
        kitsu_data = response.json()
    print(url)
    metas = []
    for item in kitsu_data.get('data', []):
        attributes = item['attributes']
        anime_type = attributes.get('subtype', '')
        metas.append({
            "id": f"kitsu:{item['id']}",
            "type": "movie" if anime_type == 'movie' else "series",
            "animeType": anime_type,
            "name": attributes['titles'].get('en') or attributes['titles'].get('en_us') or attributes['titles'].get('en_jp') or attributes['titles'].get('ja_jp'),
            "poster": attributes.get('posterImage', {}).get('small', ''),
            #"background": attributes.get('coverImage', {}).get('large'),
            "description": attributes.get('synopsis'),
            #"releaseInfo": attributes.get('startDate'),
            #"runtime": f"{attributes.get('episodeLength', 0)} min"
        })

    return json_response({"metas": metas})
        

@app.get("/meta/{type}/{id}.json")
async def get_meta(type: str, id: str):
    print(f"{kitsu_addon_url}/meta/{type}/{id}.json")
    async with httpx.AsyncClient() as client:
        reponse = await client.get(f"{kitsu_addon_url}/meta/{type}/{id}.json")
        return json_response(reponse.json())


@app.get("/manifest.json")
async def get_manifest():
    with open("manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return json_response(manifest)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 7000)))