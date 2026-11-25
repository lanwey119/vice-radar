"""Schedule one rights-cleared, quality-checked VICE RADAR video. No secret logging."""
import os, json, urllib.request, urllib.error, urllib.parse, sys
key=os.environ.get("BUFFER_API_KEY")
if not key: sys.exit("Missing Buffer secret")
def gql(query, variables=None):
    req=urllib.request.Request("https://api.buffer.com",data=json.dumps({"query":query,"variables":variables or {}}).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=45) as response: data=json.load(response)
    except urllib.error.HTTPError as e: sys.exit("Buffer HTTP "+str(e.code)+"; inspect existing posts before retry")
    if data.get("errors"): sys.exit("GraphQL query rejected; inspect existing posts before retry")
    return data["data"]
service=os.environ["TARGET"]
if service not in ("youtube","tiktok"): sys.exit("Unknown target")
matches=[]
for org in gql("query { account { organizations { id } } }")["account"]["organizations"]:
    query="query { channels(input: { organizationId: "+json.dumps(org["id"])+" }) { id service name displayName isQueuePaused } }"
    for ch in gql(query)["channels"]:
        name="".join(c for c in (str(ch.get("name") or "")+str(ch.get("displayName") or "")).lower() if c.isalnum())
        if ch["service"]==service and "viceradar" in name and not ch["isQueuePaused"]: matches.append((org["id"],ch["id"]))
if len(matches)!=1: sys.exit("Expected exactly one active VICE RADAR channel")
org,cid=matches[0]
if os.environ.get("DRY_RUN","true")=="true":
    print("Read-only preflight succeeded for "+service+". No posts created.")
    sys.exit(0)
if os.environ.get("RIGHTS_QA")!="true": sys.exit("Rights and quality clearance required")
url=os.environ["VIDEO_URL"]; title=os.environ["TITLE"]; text=os.environ["CAPTION"]; episode=os.environ["EPISODE"]
u=urllib.parse.urlparse(url)
if u.scheme!="https" or not u.netloc or not u.path.lower().endswith(".mp4") or "review" in u.path.lower(): sys.exit("Public HTTPS final MP4 required; review files are prohibited")
if not episode or not title.strip() or not text.strip(): sys.exit("Episode, title and caption required")
marker="VICE RADAR "+episode
text=text+"\n\n"+marker
cursor=None
while True:
    q="query { posts(first: 50"+(", after: "+json.dumps(cursor) if cursor else "")+", input: { organizationId: "+json.dumps(org)+", filter: { channelIds: ["+json.dumps(cid)+"], status: [draft,needs_approval,scheduled,sending,sent,error] } }) { edges { node { id text status } } pageInfo { hasNextPage endCursor } } }"
    result=gql(q)["posts"]
    for e in result["edges"]:
        if marker in e["node"]["text"]: sys.exit("Existing episode found; do not duplicate. State: "+e["node"]["status"])
    if not result["pageInfo"]["hasNextPage"]: break
    cursor=result["pageInfo"]["endCursor"]
    if not cursor: sys.exit("Invalid pagination")
metadata={"youtube":{"title":title,"categoryId":"20","type":"short","privacy":"public","madeForKids":False,"isAiGenerated":True}} if service=="youtube" else {"tiktok":{"isAiGenerated":True}}
payload={"channelId":cid,"text":text,"assets":[{"video":{"url":url}}],"metadata":metadata,"aiAssisted":True,"schedulingType":"automatic","mode":"addToQueue","needsApproval":False,"saveToDraft":False}
res=gql("mutation Schedule($input: CreatePostInput!) { createPost(input: $input) { __typename ... on PostActionSuccess { post { id status dueAt externalLink } } ... on MutationError { message } } }",{"input":payload})["createPost"]
if res["__typename"]!="PostActionSuccess": sys.exit("Buffer refused scheduling; no automatic retry")
print(json.dumps(res["post"]))
